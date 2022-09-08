from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Petfinder_API_Token, Profile, Favorite, Room
from django.contrib.auth.models import User
from .forms import CreateUserForm
from datetime import datetime, timezone
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse
import re
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
  print(url,'<-url')
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
def make_pagination(view_type, pagination_dict, current_page):
  api_url_substring = f'/v2/{view_type}'

  previous_url = '#'
  next_url = '#'
  if '_links' in pagination_dict:
    if 'previous' in pagination_dict['_links']:
      previous_query_string = pagination_dict['_links']['previous']['href']
      previous_url = previous_query_string.replace(api_url_substring, '')
    if 'next' in pagination_dict['_links']:
      next_query_string = pagination_dict['_links']['next']['href']
      next_url = next_query_string.replace(api_url_substring, '')
  pages = []
  next_string = f'page={current_page+1}'
  total_pages = pagination_dict['total_pages']
  if current_page <= 3:
    for i in range(1,6):
      if i <= total_pages:
        this_string = f'page={i}'
        page_url = next_url.replace(next_string, this_string)
        page_dict = {'page_number': i, 'page_url': page_url}
        pages.append(page_dict)
  else:
    for i in range(current_page-2, current_page+3):
      if i <= total_pages:
        this_string = f'page={i}'
        page_url = next_url.replace(next_string, this_string)
        page_dict = {'page_number': i, 'page_url': page_url}
        pages.append(page_dict)

  next_chunk_string = f'page={current_page+5}'
  next_chunk = next_url.replace(next_string, next_chunk_string)
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

  print(updated_pagination,'<-updated_pagination')
  
  return updated_pagination 

'''
View Functions
'''
def home(request): 
  response = get_petfinder_request('animals', [('type', 'dog'), ('location', '78729')])
  return render(request, 'home.html', {'response': response})

def about(request):
  return render(request, 'about.html')

@login_required
def index_view(request):
    return render(request, 'index.html', {
        'rooms': Room.objects.all(),
    })

@login_required
def room_view(request, room_name):
    chat_room, created = Room.objects.get_or_create(name=room_name)
    return render(request, 'room.html', {
        'room': chat_room,
    })

def signup(request):
  if request.user.is_authenticated:
    return redirect('profiles/detail.html')
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
        return redirect('profiles/detail.html')
      else:
        error_message = 'Invalid sign up - try again'
    # A bad POST or a GET request, so render signup.html with an empty form
    form = CreateUserForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

@login_required
def animals_index(request):
  view_type = 'animals'
  current_query_string = request.META['QUERY_STRING']
  form = request.POST
  form_query_list = [('type', 'dog')]
  form_query_list_no_escape = [('type', 'dog')]
  query_list = []
  if len(form) > 0:
    form_query_list = []
    form_query_list_no_escape = []
    for key, value in form.items():
      if key != 'csrfmiddlewaretoken' and value != '':
        # value = value.lower()
        form_query_list.append((key, urllib.parse.quote(value.lower(), safe='()')))
        form_query_list_no_escape.append((key, value.lower()))
    if form_query_list != []:
      animals = get_petfinder_request('animals', form_query_list)
      current_page = 1
  elif current_query_string:
    query_dict = request.GET
    for key, value in query_dict.items():
      query_list += (key, value[0])
    print(query_dict,'<--query_dict')
    animals = get_petfinder_request(f'{view_type}?{current_query_string}')
    current_page = int(request.GET['page'])
  else:
    animals = get_petfinder_request(view_type,[('type', 'dog')])
    current_page = 1
  
  # print(animals,'<-animals')
  if query_list:
    form_query = query_dict
  else:
    form_query = dict(form_query_list_no_escape)
  print(form_query,'<-form_query')
  if 'pagination' in animals:
    pagination = make_pagination(view_type, animals['pagination'], current_page)
  else:
    pagination = {}
  if animals:
    print(animals)
    animals_clean = clean_api_response(f'{view_type}/index', animals)
  else:
    animals_clean = {}
  return render(request, 'animals/index.html', {'animals': animals_clean, 'pagination': pagination, 'form_query': form_query})

@login_required
def animals_detail(request, animal_id):
  # retrieve all favorites for the current logged in user, and store each found favorite in a list
  listOfFavorites = User.objects.get(id=request.user.id).favorites.all()
  # now go through the list of favorites and store the id of each favorite in a list
  listOfFavoriteIds = []
  for favorite in listOfFavorites:
    listOfFavoriteIds.append(int(favorite.animal_id))
  # declare a variable to store whether or not the current animal has been favorited by the current user
  is_favorite = False
  # now check if animal_id is in the list of listOfFavoriteIds, if it is, set the is_favorite variable to True
  if int(animal_id) in listOfFavoriteIds:
    is_favorite = True

  view_type = 'animals'
  animal = get_petfinder_request(f'{view_type}/{animal_id}')
  animal_clean = clean_api_response(f'{view_type}/detail', animal)
  organization_id = animal['animal']['organization_id']
  organization = get_petfinder_request(f'organizations/{organization_id}')
  organization_clean = clean_api_response('organizations/detail', organization)
  google_map_url = get_google_map_url(organization['organization']['address'])
  return render(request, 'animals/detail.html', {'animal': animal_clean, 'organization': organization_clean, 'google_map_url': google_map_url, 'is_favorite': is_favorite})

def organizations_index(request):
  query_list = []
  if request.POST:
    for key, value in request.POST.items():
      if key != 'csrfmiddlewaretoken' and value:
        query_list.append((key, value))
  current_query_string = request.META['QUERY_STRING']
  view_type = 'organizations'
  if current_query_string:
    organizations = get_petfinder_request(f'{view_type}?{current_query_string}')
    current_page = int(request.GET['page'])
  else:
    organizations = get_petfinder_request(view_type, query_list)
    current_page = 1 
  pagination = make_pagination(view_type, organizations['pagination'], current_page) 
  return render(request, 'organizations/index.html', {'organizations': organizations, 'pagination': pagination})

def organizations_detail(request, organization_id):
  view_type = 'organizations'
  organization = get_petfinder_request(f'{view_type}/{organization_id}') 
  organization_clean = clean_api_response(f'{view_type}/detail', organization)
  animals = get_petfinder_request('animals', ['organization', organization_id])
  animals_clean = clean_api_response('animals/index', animals)
  google_map_url = get_google_map_url(organization['organization']['address'])
  return render(request, 'organizations/detail.html', {'organization': organization_clean, 'google_map_url': google_map_url, 'animals': animals_clean})

@login_required
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

def animals_search(request, query_list=''):
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

@login_required
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
    type = animal_clean['animal']['type'],
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

@login_required
def delete_favorite(request, user_id, animal_id):
  # retrieve the favorite that has the user_id and animal_id and delete it
  favorite = Favorite.objects.get(user_id=user_id, animal_id=animal_id)
  favorite.delete()
  return redirect('animals.detail', animal_id=animal_id)

@login_required
def favorites_index(request, user_id):
  # retrieve all the favorites for the currently logged in user
  favorites = Favorite.objects.filter(user_id=user_id)
  # convert all photos in favorites to lists
  for favorite in favorites:
      if favorite.photos != '[]':
          favorite.petphoto = re.search(r"'(.+?)'", favorite.photos).group(1)
      else:
          favorite.petphoto = None

  # return render the favorites.photos as a list
  return render(request, 'favorites/index.html', {'favorites': favorites})


@login_required
def favorites_detail(request, favorite_id):
  favorites = Favorite.objects.filter(id=favorite_id)
  return render(request, 'favorites/detail.html', { 'favorites': favorites })

class FavoriteDelete(LoginRequiredMixin, DeleteView):
  model = Favorite
  del Favorite.user_id
  

