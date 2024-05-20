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
    path('images/search/', views.image_search_view, name= 'Get_images_search_by_keywords'),
]

urlpatterns += router.urls