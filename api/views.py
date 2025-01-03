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
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count
from rest_framework.pagination import LimitOffsetPagination
from .houzz import scrape_houzz_images
from .planner import detect_walls_and_shapes_in_image
from pdf2image import convert_from_bytes
from io import BytesIO
from .models import ImagePrediction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import os
import requests

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

    def retrieve(self, request, *args, **kwargs):
        instance = self.queryset.filter(user=kwargs.get("pk"))
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data)
        
class ImageVariantView(ModelViewSet):
    queryset = Image_variant.objects.all()
    serializer_class = ImageVariantSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ('post', 'get')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.queryset.filter(base_image=kwargs.get("pk"))
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
        sorted_data_length = len(sorted_data)

        paginator = LimitOffsetPagination()
        result_page = paginator.paginate_queryset(sorted_data, request)

        return Response({"total": sorted_data_length,"data": result_page}, status=200)
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
        return Response({"message": "Update Image Failed!"}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_image_count(request):
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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def variant_query(request):
    image_id = request.GET.get("image_id")
    key = request.GET.get("key")
    value = request.GET.get("value")
    data = Image_variant.objects.filter(base_image = image_id)
    if value and not key:
        return Response({"message": "Invalid Variants!"}, status=400)
    elif not value and not key:
        return Response({"message": "Invalid Variants!"}, status=400)
    elif key and not value:
        data = data.filter(data__has_key = key)
        serializer = ImageVariantSerializer(data, many=True)
        return Response(serializer.data, status=200)
    elif key and value:
        filter_kwargs = {
            f'data__{key}': value
        }
        data = data.filter(**filter_kwargs)
        serializer = ImageVariantSerializer(data, many=True)
        return Response(serializer.data, status=200)        
        
    else:
        return Response({"message": "Invalid Variants!"}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def Image_list(request):
    queryset = Image_variant.objects.all().distinct('base_image_id')
    image_id_list = []
    for each in queryset:
        image_id_list.append(each.base_image)
    instance_list = []
    for each in image_id_list:
        try:
            data = Image_file.objects.get(id=each.id)
            serializer = ImageFileSerializer(data)
        except:
            data =  Image_url.objects.get(id=each.id)
            serializer = ImageURLSerializer(data)
        
        instance_list.append(serializer.data)
    
    return Response(instance_list)
    
@api_view(['get'])
@permission_classes([IsAuthenticated])
def get_houzz_images(request):
    try:
        keyword = request.query_params.get('query')
        page = int(request.query_params.get('page_number'))
    except:
        return Response("Query params missing", status=400)
    
    images = scrape_houzz_images(keyword, page)
    json_response = {
        "images": images
    }
    
    return Response(json_response, status=200)

@api_view(['POST'])
def shapes_and_wall_detection_api(request):
    if request.method == 'POST':
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            if image_file.content_type.startswith('image/'):
                res = detect_walls_and_shapes_in_image(image_file)
                return Response(json.loads(res), status=200)
            elif image_file.content_type == 'application/pdf':
                pdf_bytes = image_file.read()
                images = convert_from_bytes(pdf_bytes)

                combined_results = {}
                for page_number, image in enumerate(images, start=1):
                    image_bytes = BytesIO()
                    image.save(image_bytes, format='JPEG')
                    image_bytes.seek(0)

                    page_result = detect_walls_and_shapes_in_image(image_bytes)
                    floor_key = f"Floor {page_number}"
                    combined_results[floor_key] = json.loads(page_result)
                    print(f"Processed {floor_key}")

                return Response(combined_results, status=200)

        return Response({"error": "Unsupported file type. Please provide an image or a PDF."}, status=400)

    return Response({"error": "Invalid request method."}, status=405)

@api_view(['POST'])
def create_or_update_prediction(request):
    if request.method == "POST":
        data = json.loads(request.body)

        if "imageID" in data and "prediction1ID" in data:
            imageID = data["imageID"]
            prediction1ID = data["prediction1ID"]
            obj = ImagePrediction.objects.create(imageID=imageID, prediction1ID=prediction1ID)
            return JsonResponse({"message": "Row created", "id": obj.id}, status=201)

        elif "prediction1ID" in data and "prediction2ID" in data:
            prediction1ID = data["prediction1ID"]
            prediction2ID = data["prediction2ID"]
            obj = get_object_or_404(ImagePrediction, prediction1ID=prediction1ID)
            obj.prediction2ID = prediction2ID
            obj.save()
            return JsonResponse({"message": "Row updated with prediction2ID"}, status=200)

        elif "prediction2ID" in data and "imageURL" in data:
            prediction2ID = data["prediction2ID"]
            imageURL = data["imageURL"]
            obj = get_object_or_404(ImagePrediction, prediction2ID=prediction2ID)
            obj.imageURL = imageURL
            obj.save()
            return JsonResponse({"message": "Row updated with imageURL"}, status=200)

        return JsonResponse({"error": "Invalid data"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@api_view(['get'])
def get_image_url(request):
    if request.method == "GET":
        imageID = request.GET.get("imageID")

        if not imageID:
            return JsonResponse({"error": "imageID is required"}, status=400)

        obj = ImagePrediction.objects.filter(imageID=imageID).first()

        if not obj:
            return JsonResponse({"error": "No record found"}, status=404)

        return JsonResponse({"imageURL": obj.imageURL if obj.imageURL else "pending"}, status=200)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def dwg_parser(request):
    if request.method == "POST":
        dwg_file = request.FILES.get("file", None)
        print(dwg_file)
        if not dwg_file:
            return JsonResponse({"error": "No DWG file provided under field 'file'."}, status=400)
        
        try:
            convertapi_url = "https://v2.convertapi.com/convert/dwg/to/svg"
            params = {"secret": os.getenv('CONVERTAPI')}
            
            form_data = {
                "storefile": "true",
                "ImageHeight": "1024",
                "ImageWidth": "1280",
                "ColorSpace": "grayscale",
            }

            files = {
                "file": (dwg_file.name, dwg_file.read(), dwg_file.content_type),
            }

            response = requests.post(
                convertapi_url,
                params=params,
                data=form_data,
                files=files,
            )

            if response.status_code == 200:
                converted_data = response.json()
                return JsonResponse({"convertapi_result": converted_data}, status=200)

            else:
                return JsonResponse(
                    {
                        "error": "ConvertAPI call failed",
                        "status_code": response.status_code,
                        "details": response.text
                    },
                    status=500
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    return JsonResponse({"error": "Method not allowed"}, status=405)

