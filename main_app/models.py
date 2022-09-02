from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Petfinder_API_Token(models.Model):
  token = models.TextField()
  date = models.DateTimeField(auto_now=True)

class Profile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  name = models.CharField(max_length=24)
  bio = models.TextField(max_length=240)

  def __str__(self):
    return self.name
