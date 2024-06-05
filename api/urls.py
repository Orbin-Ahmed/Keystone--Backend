from django.urls import path
from . import views
from rest_framework import routers


router = routers.SimpleRouter()
router.register(r'register', views.UserView, basename='CRUD User')
router.register(r'company', views.CompanyView, basename='CRUD Comapny Info')
router.register(r'social', views.SocialLinkView, basename='CRUD Social Info')
router.register(r'variants', views.ImageVariantView, basename='Get and Post Image variants')

urlpatterns = [
    path('login/', views.login_view, name= 'login'),
    path('logout/', views.logout_view, name= 'logout'),
    path('token/', views.user_token, name= 'user_info_by_token'),
    path('images/search/', views.image_search_view, name= 'get_images_search_by_keywords'),
    path('images/url/', views.post_images_url, name= 'post_image_by_url'),
    path('images/file/', views.post_image_file, name= 'post_image_by_file'),
    path('images/', views.get_images, name= 'get_all_image_update_image'),
    path('social/update/', views.update_socials, name= 'update_social_links'),
    path('total/images/', views.get_image_count, name= 'total_image_count'),
    path('variants/filter/', views.variant_query, name= 'filter_variant_by_key_value'),
    path('variants/image/', views.Image_list, name= 'get_base_image_list_of_variants'),
]

urlpatterns += router.urls