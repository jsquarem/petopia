from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

# Create your models here.
class Petfinder_API_Token(models.Model):
  token = models.TextField()
  date = models.DateTimeField(auto_now=True)

class Profile(models.Model):
  user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
  name = models.CharField(max_length=24)
  bio = models.TextField(max_length=240)

  def __str__(self):
    return self.name

  def get_absolute_url(self):
    return reverse('detail', kwargs={'user_id': self.user.id})

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

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    animal_id = models.TextField()
    name = models.TextField(null=True)
    gender = models.TextField(null=True)
    age = models.TextField(null=True)
    breed = models.TextField(null=True)
    size = models.TextField(null=True)
    sterile = models.TextField(null=True)
    shots = models.TextField(null=True)
    description = models.TextField(null=True)
    tags = models.TextField(null=True)
    photos = models.TextField(null=True)
    env_dogs = models.TextField(null=True)
    env_cats  = models.TextField(null=True)
    env_child = models.TextField(null=True)
    org_name = models.TextField(null=True)
    org_mission  = models.TextField(null=True)
    org_city = models.TextField(null=True)
    org_state = models.TextField(null=True)
    org_email = models.TextField(null=True)
    org_phone = models.TextField(null=True)
    org_url = models.TextField(null=True)

    def __str__(self):
      return self.name