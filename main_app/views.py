from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Petfinder_API_Token, Profile
from .forms import CreateUserForm
from datetime import datetime, timezone
import requests
from requests.structures import CaseInsensitiveDict
import os
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

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
def get_petfinder_request(endpoint = '', query_list = ''):
  url = 'https://api.petfinder.com/v2/'
  url = url + endpoint
  query_string = ''
  if query_list:
    for i, query in enumerate(query_list):
      if i == 0:
        query_string = query_string + f'?{query[0]}={query[1]}'
      else:
        query_string = query_string + f'&{query[0]}={query[1]}'
  url = url + query_string
  token = get_petfinder_token()
  headers = CaseInsensitiveDict()
  headers["Accept"] = "application/json"
  headers["Authorization"] = f"Bearer {token}"
  response = requests.get(url, headers=headers)
  return response.json()
  


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
  response = get_petfinder_request('animals')
  return render(request, 'animals/index.html', {'response': response})


def animals_detail(request, animal_id):
  response = get_petfinder_request(f'animals/{animal_id}')  
  return render(request, 'animals/detail.html', {'response': response})

def organizations_index(request):
  pass

def organizations_detail(request):
  pass

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