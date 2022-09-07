from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Petfinder_API_Token, Profile, Favorite
from django.contrib.auth.models import User
from .forms import CreateUserForm
from datetime import datetime, timezone
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse
import requests
import os
import json

'''
Petfinder API Functions
'''
def update_petfinder_token():
  load_dotenv()
  PETFINDER_API_KEY = os.getenv('PETFINDER_API_KEY')
  PETFINDER_SECRET = os.getenv('PETFINDER_SECRET')
  url = 'https://api.petfinder.com/v2/oauth2/token'
  payload = { 'grant_type': 'client_credentials', 'client_id':{PETFINDER_API_KEY}, 'client_secret':{PETFINDER_SECRET} }
  response = requests.post(url, data = payload)
  response = response.json()
  return response['access_token']
  
def get_petfinder_token():
  token_object = Petfinder_API_Token.objects.first()
  # TODO update timezone awareness if we set a server timezone/use tomezones
  token_age = datetime.now(timezone.utc) - token_object.date
  print(token_age.total_seconds(), '<- Token Age')
  if token_age.total_seconds() >= 3000:
    token_object.token = update_petfinder_token()
    token_object.save()
  return token_object.token

# query_list expects a list of key, value tuples ex. [(key, value), (key2, value2), ...]
def get_petfinder_request(endpoint = '', query_list = []):
  url = 'https://api.petfinder.com'
  if '/v2/' not in endpoint:
    url += '/v2/'
  url += endpoint
  query_string = ''
  if len(query_list) > 0:
    for i, query in enumerate(query_list):
      modifier = '?' if i == 0 else '&'
      query_string += f'{modifier}{query[0]}={query[1]}'
  url +=  query_string
  token = get_petfinder_token()
  headers = CaseInsensitiveDict()
  headers["Accept"] = "application/json"
  headers["Authorization"] = f"Bearer {token}"
  response = requests.get(url, headers=headers)
  # print(response.json(), '<-response.json()')
  return response.json()

def get_expanded_description(url, type):
  # type = 'animal'
    # url = 'https://www.petfinder.com/dog/violet-56891221/ca/oakdale/city-of-oakdale-animal-shelter-ca731/?referrer_id=8a971326-6e94-4e90-aa32-70d9748109bd'
  response = requests.get(url)
  soup = BeautifulSoup(response.content, 'html.parser')  
  if type == 'animal':
    description = soup.select('div[data-test="Pet_Story_Section"]')
    description = description[0].contents[3]
    description = description.contents[0].strip()
  if type == 'organization':
    mission_elements = soup.find('h2', string='Our Mission')
    mission_sibling = mission_elements.find_next_siblings('p')
    description = mission_sibling[0].text.strip()
  return description

# Valid values for the view areguement are: 'animal/detail', 'animal/index', 'organization/detail', and 'organization/index'
def clean_api_response(view, data):  
  if view == 'animals/detail':
    description = data['animal']['description']
    name = data['animal']['name']
    type = data['animal']['type']    
    if description is None or description == '':  
      description = f'{name} the {type} is looking to share their love with you.'
    if description and description.endswith('...'):
      url = data['animal']['url']
      description = get_expanded_description(url, 'animal')
    if len(name) > 15:
      data['animal']['name'] = 'Captain Cuddles'    
    data['animal']['description'] = description
  
  if view == 'animals/index':
    for i, animal in enumerate(data['animals']):
      name = animal['name']
      if len(name) > 15:
        data['animals'][i]['name'] = 'Captain Cuddles'
  
  if view == 'organizations/detail':
    description = data['organization']['mission_statement']        
    if description is None or description == '':
      organization_name = data['organization']['name']
      description = f'{organization_name} is a cool place to adopt pets.'
    if description and description.endswith('...'):
      url = data['organization']['url']
      description = get_expanded_description(url, 'organization')    
    data['organization']['mission_statement'] = description
  return data


'''
Google Maps API Function
''' 
def get_google_map_url(address):
  url = 'https://www.google.com/maps/embed/v1/place?key=AIzaSyDbzW3rRuc7De1RF3wP0UGbsyj-pZbMbuQ&q='
  query_string = ''
  for i, (key, value) in enumerate(address.items()):
    if value != None and key != 'country':
      value = value.replace(' ', '+')
      # add comma between query address values except for last value
      query_string = query_string + f"{value}," if i < (len(address.items())-2) else query_string + f"{value}"
  return url + query_string

'''
Helper Functions
'''
def make_pagination(pagination_dict, current_page):
  if 'previous' in pagination_dict['_links']:
    previous_query_string = pagination_dict['_links']['previous']['href']
    previous_url = previous_query_string.replace('/v2/animals', '')
  else:
    previous_url = '#'
  if 'next' in pagination_dict['_links']:
    next_query_string = pagination_dict['_links']['next']['href']
    next_url = next_query_string.replace('/v2/animals', '')
  else:
    next_url = '#'
  pages = []
  next_string = f'page={current_page+1}'
  if current_page <= 3:
    for i in range(1,6):
      this_string = f'page={i}'
      page_url = next_url.replace(next_string, this_string)
      page_dict = {'page_number': i, 'page_url': page_url}
      pages.append(page_dict)
  else:
    for i in range(current_page-2, current_page+3):
      this_string = f'page={i}'
      page_url = next_url.replace(next_string, this_string)
      page_dict = {'page_number': i, 'page_url': page_url}
      pages.append(page_dict)

  next_chunk_string = f'page={current_page+5}'
  next_chunk = next_url.replace(next_string, next_chunk_string)
  total_pages = pagination_dict['total_pages']
  total_pages_string = f'page={total_pages}'
  last_page_url = next_url.replace(next_string, total_pages_string)
  last_page = {'page_number': total_pages, 'page_url': last_page_url}

  updated_pagination = {
    'next_url': next_url,
    'previous_url': previous_url,
    'current_page': current_page,
    'next_chunk': next_chunk,
    'last_page': last_page,
    'pages': pages
    }
  
  return updated_pagination 

'''
View Functions
'''
def home(request): 
  response = get_petfinder_request('animals', [('type', 'dog'), ('location', '78729')])
  return render(request, 'home.html', {'response': response})

def about(request):
  return render(request, 'about.html')

def signup(request):
  if request.user.is_authenticated:
    return redirect('home')
  else:
    error_message = ''
    if request.method == 'POST':
      # This is how to create a 'user' form object
      # that includes the data from the browser
      form = CreateUserForm(request.POST)
      if form.is_valid():
        # This will add the user to the database
        user = form.save()
        username = form.cleaned_data.get('username')
        messages.success(request, 'Account successfully created for ' + username + '.')
        # This is how we log a user in via code
        login(request, user)
        return redirect('home')
      else:
        error_message = 'Invalid sign up - try again'
    # A bad POST or a GET request, so render signup.html with an empty form
    form = CreateUserForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

def animals_index(request):
  current_query_string = request.META['QUERY_STRING']
  if current_query_string:
    animals = get_petfinder_request(f'animals?{current_query_string}')
    current_page = int(request.GET['page'])
  else:
    animals = get_petfinder_request('animals',[('type', 'dog')])
    current_page = 1
  pagination = make_pagination(animals['pagination'], current_page) 
  animals_clean = clean_api_response('animals/index', animals)
  return render(request, 'animals/index.html', {'animals': animals_clean, 'pagination': pagination})

def animals_detail(request, animal_id):
  animal = get_petfinder_request(f'animals/{animal_id}')
  animal_clean = clean_api_response('animals/detail', animal)
  organization_id = animal['animal']['organization_id']
  organization = get_petfinder_request(f'organizations/{organization_id}')
  organization_clean = clean_api_response('organizations/detail', organization)
  google_map_url = get_google_map_url(organization['organization']['address'])
  return render(request, 'animals/detail.html', {'animal': animal_clean, 'organization': organization_clean, 'google_map_url': google_map_url})

def organizations_index(request):
  current_query_string = request.META['QUERY_STRING']
  if current_query_string:
    animals = get_petfinder_request(f'ogranizations?{current_query_string}')
    current_page = int(request.GET['page'])
  else:
    organizations = get_petfinder_request('organizations/') 
    current_page = 1 
  pagination = make_pagination(organizations['pagination'], current_page) 
  return render(request, 'organizations/index.html', {'organizations': organizations})

def organizations_detail(request, organization_id):
  organization = get_petfinder_request(f'organizations/{organization_id}') 
  organization_clean = clean_api_response('organizations/detail', organization)
  animals = get_petfinder_request('animals', ['organization', organization_id])
  animals_clean = clean_api_response('animals/index', animals)
  google_map_url = get_google_map_url(organization['organization']['address'])
  return render(request, 'organizations/detail.html', {'organization': organization_clean, 'google_map_url': google_map_url, 'animals': animals_clean})

def profiles_detail(request, user_id):
  profile = Profile.objects.get(user_id=user_id)
  return render(request, 'profiles/detail.html', { 'profile': profile })


class ProfileCreate(LoginRequiredMixin, CreateView):
  model = Profile
  fields = ['name', 'bio']
  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class ProfileUpdate(LoginRequiredMixin, UpdateView):
  model = Profile
  fields = ['name', 'bio']

class ProfileDelete(LoginRequiredMixin, DeleteView):
  model = Profile
  success_url = '/profiles/create/'

def add_photo(request):
  pass

# def add_favorite(request):
#   pass

def delete_favorite(request):
  pass

def lobby(request):
  return render(request, 'profiles/lobby.html')

def animals_search(request):
  animals = get_petfinder_request('animals')
  form = request.POST
  if len(form) > 0:
    query_list = []
    for key, value in form.items():
      if key != 'csrfmiddlewaretoken' and value != '':
        query_list.append((key, urllib.parse.quote(value)))
    if query_list != []:
      animals = get_petfinder_request('animals', query_list)
  return render(request, 'animals/search_test.html', {'animals': animals})

def contact(request):
  if request.method == 'POST':
    confirmation = {}
    message_name = request.POST['name']
    message_email = request.POST['email']
    message = request.POST['message']
    send_mail(
      f'Contact Request - {message_name}',
      message,
      message_email,
      ['jeffjmart@gmail.com']
    )
    confirmation['message'] = 'Thank you for yor message, we will respond as soon as we can.'
    confirmation['name'] = message_name
    return render(request, 'contact.html', {'confirmation': confirmation})
  else:
    return render(request, 'contact.html')

# class Favorite:
#   def __init__(self, user_id, animal_id, name, gender, age, breed, size, sterile, shots, description, tags, photos, env_dogs, env_cats, env_child, org_name, org_mission, org_city, org_state, org_email, org_phone, org_url):
#     self.user_id = user_id
#     self.animal_id = animal_id
#     self.name = name
#     self.gender = gender
#     self.age = age
#     self.breed = breed
#     self.size = size
#     self.sterile = sterile
#     self.shots = shots
#     self.description = description
#     self.tags = tags
#     self.photos = photos
#     self.env_dogs = env_dogs
#     self.env_cats = env_cats 
#     self.env_child = env_child
#     self.org_name = org_name
#     self.org_mission = org_mission 
#     self.org_city = org_city
#     self.org_state = org_state
#     self.org_email = org_email
#     self.org_phone = org_phone
#     self.org_url = org_url

#   def __str__(self):
#     return self.name

  # @classmethod
  # def from_json(cls, json_string):
  #   json_dict = json.loads(json_string)
  #   return Favorite(**json_dict)

  # def __repr__(self):
  #   return f'<Favorite { self.name }>'


def add_favorite(request, user_id, animal_id):
  animal = get_petfinder_request(f'animals/{animal_id}')
  animal_clean = clean_api_response('animals/detail', animal)
  organization_id = animal['animal']['organization_id']
  organization = get_petfinder_request(f'organizations/{organization_id}')
  organization_clean = clean_api_response('organizations/detail', organization)
  google_map_url = get_google_map_url(organization['organization']['address'])
  photo_list = animal['animal']['photos']
  new_photo_list = []
  for photo in photo_list:
    photo_url = photo['full']
    new_photo_list.append(photo_url)
  print(new_photo_list, '<- Photo List')
  
  new_favorite = Favorite.objects.create(
    user = User.objects.get(id=user_id),
    animal_id=animal_clean['animal']['id'],
    name=animal_clean['animal']['name'],
    gender=animal_clean['animal']['gender'],
    age=animal_clean['animal']['age'],
    breed=animal_clean['animal']['breeds']['primary'],
    size=animal_clean['animal']['size'],
    sterile=animal_clean['animal']['attributes']['spayed_neutered'],
    shots=animal_clean['animal']['attributes']['shots_current'],
    description=animal_clean['animal']['description'],
    tags=animal_clean['animal']['tags'],
    photos = new_photo_list,
    env_dogs=animal_clean['animal']['environment']['dogs'],
    env_cats=animal_clean['animal']['environment']['cats'],
    env_child=animal_clean['animal']['environment']['children'],
    org_name=organization_clean['organization']['name'],
    org_mission=organization_clean['organization']['mission_statement'],
    org_city=organization_clean['organization']['address']['city'],
    org_state=organization_clean['organization']['address']['state'],
    org_email=organization_clean['organization']['email'],
    org_phone=organization_clean['organization']['phone'],
    org_url=organization_clean['organization']['url']
  )
  print(new_favorite, '<- New Favorite Animal')
  return redirect('animals.detail', animal_id=animal_id)


def favorites_index(request, user_id):
  favorites = Favorite.objects.get(user_id=user_id)
  return render(request, 'favorites/index.html', { 'favorites': favorites })

def favorites_detail(request, favorite_id):
  favorites = Favorite.objects.get(id=favorite_id)
  return render(request, 'favorites/detail.html', { 'favorites': favorites })

class FavoriteDelete(DeleteView):
  model = Favorite
  del Favorite.user_id
  #or maybe Favorite.favorite_id
  # success_url: '/profile/user_id/favorites/'

