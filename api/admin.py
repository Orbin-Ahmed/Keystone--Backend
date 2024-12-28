from django.contrib import admin
from . import models
from django.contrib.auth.models import Group

class UserAdmin(admin.ModelAdmin):
    pass

class ImageFileAdmin(admin.ModelAdmin):
    pass

class ImageURLAdmin(admin.ModelAdmin):
    pass

class RegisterTokenAdmin(admin.ModelAdmin):
    pass

class PasswordTokenAdmin(admin.ModelAdmin):
    pass

class SocialLinkAdmin(admin.ModelAdmin):
    pass

class VariantBaseAdmin(admin.ModelAdmin):
    pass

class ImagePredictionAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Image_file, ImageFileAdmin)
admin.site.register(models.Image_url, ImageURLAdmin)
admin.site.register(models.Social_link, SocialLinkAdmin)
admin.site.register(models.Image_variant, VariantBaseAdmin)
admin.site.register(models.ImagePrediction, ImagePredictionAdmin)
admin.site.unregister(Group)
