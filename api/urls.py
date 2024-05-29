from django.urls import path
from . import views
from rest_framework import routers


router = routers.SimpleRouter()
router.register(r'register', views.UserView, basename='CRUD User')
router.register(r'company', views.CompanyView, basename='CRUD Comapny Info')
router.register(r'social', views.SocialLinkView, basename='CRUD Social Info')

urlpatterns = [
    path('login/', views.login_view, name= 'login'),
    path('logout/', views.logout_view, name= 'logout'),
    path('token/', views.user_token, name= 'user_info_by_token'),
    path('images/search/', views.image_search_view, name= 'get_images_search_by_keywords'),
    path('images/url/', views.post_images_url, name= 'post_image_by_url'),
    path('images/file/', views.post_image_file, name= 'post_image_by_file'),
    path('images/', views.get_images, name= 'get_all_image_update_image'),
]

urlpatterns += router.urls