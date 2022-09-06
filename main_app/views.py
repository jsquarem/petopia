from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Petfinder_API_Token, Profile
from .forms import CreateUserForm
from datetime import datetime, timezone
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse
import requests
import os

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
  url = 'https://api.petfinder.com/v2/'
  url = url + endpoint
  query_string = ''
  if len(query_list) > 0:
    for i, query in enumerate(query_list):
      modifier = '?' if i == 0 else '&'
      query_string = query_string + f'{modifier}{query[0]}={query[1]}'
  url = url + query_string
  token = get_petfinder_token()
  headers = CaseInsensitiveDict()
  headers["Accept"] = "application/json"
  headers["Authorization"] = f"Bearer {token}"
  response = requests.get(url, headers=headers)
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
    print('in organization')
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
  animals = get_petfinder_request('animals')  
  animals_clean = clean_api_response('animals/index', animals)
  return render(request, 'animals/index.html', {'animals': animals_clean})

def animals_detail(request, animal_id):
  animal = get_petfinder_request(f'animals/{animal_id}')
  animal_clean = clean_api_response('animals/detail', animal)
  organization_id = animal['animal']['organization_id']
  organization = get_petfinder_request(f'organizations/{organization_id}')
  organization_clean = clean_api_response('organizations/detail', organization)
  google_map_url = get_google_map_url(organization['organization']['address'])
  return render(request, 'animals/detail.html', {'animal': animal_clean, 'organization': organization_clean, 'google_map_url': google_map_url})

def organizations_index(request):
  organizations = get_petfinder_request('organizations/')  
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

def add_favorite(request):
  pass

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

