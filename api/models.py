from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=255)
    role = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photo/',blank=True, null=True)

class Social_link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(max_length=255, blank=True, null=True)

class Company(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    license = models.CharField(max_length=255, blank=True, null=True)
    company_intro = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='photo/',blank=True, null=True)

class Image(models.Model):
    source = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    room_type = models.CharField(max_length=255, null=True, blank=True)
    style = models.CharField(max_length=255, null=True, blank=True)
    theme = models.CharField(max_length=255, null=True, blank=True)
    object_type = models.CharField(max_length=255, null=True, blank=True)
    is_url = models.BooleanField(null=True, blank=True)
    is_object = models.BooleanField(null=True, blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class meta:
        abstract = True

class Image_file(Image):
    photo = models.ImageField(upload_to='pin/', blank=True, null=True)

class Image_url(Image):
    photo = models.URLField(max_length=255, blank=True, null = True)
    

class Image_variant(models.Model):
    base_image = models.ForeignKey(Image, on_delete=models.CASCADE)
    data = models.JSONField(max_length=255, blank=True, null=True)
    variant_image = models.ImageField(upload_to='pin/', blank=True, null=True)