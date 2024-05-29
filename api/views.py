import json
from django.contrib.auth import authenticate, login
from .models import User, Company, Social_link, Image_url, Image_file, Image
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import ModelViewSet
from .serializer import *
from django.contrib.auth.models import AnonymousUser
from .scrapper import search_pinterest
from rest_framework.parsers import MultiPartParser
from django.db.models import Count

# Create your views here.
# 0 = super User 
# 1 = Admin 
# 2 = Moderator 
# 3 = Designer 

class UserView(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserPostSerializer
    permission_classes = [AllowAny]
    http_method_names = ('post', 'get', 'patch', 'put')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'destroy':
            return UserPostSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserPostSerializer
        else:
            return UserFetchSerializer
        
    def get_permissions(self):
        if self.action == 'list':
            if(self.request.user==AnonymousUser()):
                permission_classes = [IsAdminUser]
            elif(self.request.user.role != 1):
                permission_classes = [IsAdminUser]
            else:
                permission_classes = self.permission_classes
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        if 'password' in self.request.data:
            password = make_password(self.request.data['password'])
        else:
            return Response("Invalid password provided", status=400)
        serializer.validated_data['password'] = password
        user_object = serializer.save()

    def perform_update(self, serializer):
        if 'password' in self.request.data:
            password = make_password(self.request.data['password'])
            serializer.validated_data['password'] = password
        serializer.save()


class CompanyView(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ('post', 'get', 'patch', 'put')

    def get_permissions(self):
        if self.action == 'retrieve':
            if(self.request.user==AnonymousUser()):
                permission_classes = [AllowAny]
            else:
                permission_classes = self.permission_classes
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]
    

class SocialLinkView(ModelViewSet):
    queryset = Social_link.objects.all()
    serializer_class = SocialLinkGetSerializer
    permission_classes = [AllowAny]
    http_method_names = ('get')

    # def get_permissions(self):
    #     if self.action == 'retrieve':
    #         if(self.request.user==AnonymousUser()):
    #             permission_classes = [AllowAny]
    #         else:
    #             permission_classes = self.permission_classes
    #     else:
    #         permission_classes = self.permission_classes
    #     return [permission() for permission in permission_classes]

    # def get_serializer_class(self):
    #    if self.action == "retreive":
    #        return self.serializer_class
    #    elif self.action == "update" or "create":
    #        return 


    def retrieve(self, request, *args, **kwargs):
        print(kwargs)
        instance = self.queryset.filter(user=kwargs.get("pk"))
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data)
        
@api_view(['post'])
@permission_classes([IsAuthenticated])
def update_socials(request):
    the_list = Social_link.objects.filter(user=request.user.id)
    for each in the_list:
        each.delete()
    the_list = []
    for i in request.data:
        social_object = Social_link.objects.create(user=request.user, platform=i.get("platform"), link=i.get("link"))
        the_list.append(social_object)
    return Response("done", status=200)

@api_view(['post'])
def login_view(request):
    try:
        username = request.data['username']
        password = request.data['password']
    except:
        return Response("All field is required", status=404)
    try:
        user = authenticate(request, username=username, password=password)
    except:
        return Response("Invalid credentials", status=404)
    if user is None:
        return Response("Invalid credentials", status=401)
    else:
        login(request, user)
        try:
            Token.objects.filter(user=user).delete()
        except:
            pass
        token = Token.objects.create(user=user)
        return Response({"Token": token.key}, status=200)

@api_view(['get'])
@permission_classes([IsAuthenticatedOrReadOnly])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response({"message": "User logout successfull."}, status=200)

@api_view(['get'])
@permission_classes([IsAuthenticated])
def user_token(request):
    serializer = UserFetchSerializer(request.user)
    return Response(serializer.data, status=200)

@api_view(['get'])
@permission_classes([IsAuthenticated])
def image_search_view(request):
    try:
        query = request.query_params.get('query')
        page_size = int(request.query_params.get('page_size'))
        page_number = int(request.query_params.get('page_number'))
    except:
        return Response("Query params missing", status=404)
    res = search_pinterest(query, page_size, page_number)
    return Response(res, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_images_url(request):
    serializer = ImageURLSerializer(data = request.data, many=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.validated_data)
    else:
        return Response(serializer.errors, status=400)
    
@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def post_image_file(request):
    serializer = ImageFileSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_images(request):
    if request.method == 'GET':
        room_type = request.GET.get('room_type')
        source = request.GET.get('source')

        image_files = Image_file.objects.all()
        image_urls = Image_url.objects.all()

        if room_type:
            room_type = room_type.lower()
            image_files = image_files.filter(room_type=room_type)
            image_urls = image_urls.filter(room_type=room_type)

        if source:
            image_files = image_files.filter(source=source)
            image_urls = image_urls.filter(source=source)
        
        image_file_serializer = ImageFileSerializer(image_files, many=True)
        image_url_serializer = ImageURLSerializer(image_urls, many=True)
        
        data = []

        for item in image_file_serializer.data:
            data.append(item)
        
        for item in image_url_serializer.data:
            data.append(item)
        
        sorted_data = sorted(data, key=lambda x:x['created_at'], reverse=True)

        return Response(sorted_data)
    elif request.method == "POST":
        id = request.data.get("id")
        is_url = request.data.get("is_url")
        photo = request.data.get("photo")
        if is_url is True:
            the_object = Image_url.objects.get(id=id)
            serializer = ImageURLSerializer(the_object, data = request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)       
        else:
            the_object = Image_file.objects.get(id=id)
            serializer = ImageFileSerializer(the_object)
            data = serializer.data.copy()
            data["photo"] = photo
            new_serializer = ImageURLSerializer(data=data)
            new_serializer.is_valid(raise_exception=True)
            the_object.delete()
            new_serializer.save()
            return Response(new_serializer.data)
    else:
        raise Exception("PROBLEM")


@api_view(["GET"])
def get_queryset(request):
    count =  Image_file.objects.all().count() + Image_url.objects.all().count()
    image_file_count = Image_file.objects.values("room_type", "source").annotate(count=Count("id"))
    image_url_count =  Image_url.objects.values("room_type", "source").annotate(count=Count("id"))
    data = []
    for item in image_file_count:
        data.append(item)
    
    for item in image_url_count:
        data.append(item)
    return Response({"count" : count,
                     "values": data}, status=200)

