from django.db import models

# Create your models here.
class Petfinder_API_Token(models.Model):
  token = models.TextField()
  date = models.DateTimeField(auto_now=True)

