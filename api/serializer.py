from rest_framework import serializers
from .models import Image_variant, User, Company, Social_link, Image_url, Image, Image_file

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
        
class SocialLinkGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Social_link
        fields = ('id',
                  'user',
                  'platform',
                  'link',
                  )   
        
class ImageFileSerializer(serializers.ModelSerializer):
    photo= serializers.ImageField(max_length=None, allow_null=True, use_url=True, required=True)

    class Meta:
        model = Image_file
        fields = ('id', 'photo', 'source', 'nationality', 'room_type',
                   'theme',  'is_url', 'created_at') 
    
    def create(self, validated_data):
        if 'room_type' in validated_data:
            validated_data['room_type'] = validated_data.get('room_type', '').lower()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'room_type' in validated_data:
            validated_data['room_type'] = validated_data.get('room_type', '').lower()
        return super().update(instance, validated_data)
        
class ImageURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image_url
        fields = '__all__'
    
    def create(self, validated_data):
        if 'room_type' in validated_data:
            validated_data['room_type'] = validated_data.get('room_type', '').lower()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'room_type' in validated_data:
            validated_data['room_type'] = validated_data.get('room_type', '').lower()
        return super().update(instance, validated_data)
    
class ImageVariantSerializer(serializers.ModelSerializer):
    variant_image = serializers.ImageField(max_length=None, allow_null=True, use_url=True, required=True)

    class Meta:
        model = Image_variant
        fields = ('base_image', 'data', 'variant_image')