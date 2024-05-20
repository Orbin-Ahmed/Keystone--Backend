from django.contrib.auth import authenticate, login
from .models import User, Company, Social_link
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import ModelViewSet
from .serializer import UserPostSerializer, UserFetchSerializer, CompanySerializer, SocialLinkSerializer
from django.contrib.auth.models import AnonymousUser
from .scrapper import search_pinterest

# Create your views here.
# 0 = super User 
# 1 = Admin 
# 2 = Moderator 
# 3 = Designer 

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

@api_view(['get'])
@permission_classes([IsAuthenticated])
def user_token(request):
    serializer = UserFetchSerializer(request.user)
    return Response(serializer.data, status=200)


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
    serializer_class = SocialLinkSerializer
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
    
@api_view(['get'])
@permission_classes([IsAuthenticated])
def image_search_view(request):
    try:
        query = request.query_params.get('query')
        page_size = int(request.query_params.get('page_size'))
    except:
        return Response("Query params missing", status=404)
    res = search_pinterest(query, page_size)
    return Response(res, status=200)

