from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=255)
    role = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photo/',blank=True, null=True)

class Social_link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50, blank=True, null=True)
    link = models.URLField(max_length=50, blank=True, null=True)

class Company(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    license = models.CharField(max_length=50, blank=True, null=True)
    company_intro = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='photo/',blank=True, null=True)

class Image(models.Model):
    img_url = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    room_type = models.CharField(max_length=50, null=True, blank=True)
    temperature = models.CharField(max_length=50, null=True, blank=True)
    theme = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)