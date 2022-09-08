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
    return reverse('detail.profile', kwargs={'user_id': self.user.id})

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    type = models.TextField(null=True)
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


class Room(models.Model):
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def leave(self, user):
        self.online.remove(user)
        self.save()

    def __str__(self):
        return f'{self.name} ({self.get_online_count()})'


class Message(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content} [{self.timestamp}]'