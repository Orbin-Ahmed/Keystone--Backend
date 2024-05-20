from rest_framework import serializers
from .models import User, Company, Social_link

class UserPostSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'role',
                  'is_active',
                  'full_name',
                  'phone',
                  'bio',
                  'password',
                  'photo'
                  )


class UserFetchSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(max_length=None, allow_null=True, use_url=True, required=False)

    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'role',
                  'is_active',
                  'full_name',
                  'phone',
                  'bio',
                  'photo'
                  )
        
class CompanySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, allow_null=True, use_url=True, required=False)

    class Meta:
        model = Company
        fields = ('id',
                  'name',
                  'email',
                  'phone',
                  'license',
                  'company_intro',
                  'logo'
                  )
        
class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Social_link
        fields = ('id',
                  'platform',
                  'link',
                  )