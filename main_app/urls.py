from django.urls import path
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('accounts/signup/', views.signup, name='signup'),
  path('animals/', views.animals_index, name='animals.index'),
  path('animals/<int:animal_id>/', views.animals_detail, name='animals.detail'),
  path('profile/<int:user_id>/', views.view_profile, name ='profile'),
  path('profile/create/', views.create_profile, name='create_profile'),
  path('organizations/', views.organizations_index, name='organizations.index'),
  path('organizations/<int:organization_id>/', views.organizations_detail, name='organizations.detail'),
  path('about/', views.about, name='about'),
  path('profile/<int:user_id>/add_photo/', views.add_photo, name='add_photo'),
  path('profile/<int:user_id>/add_favorite/<int:animal_id>', views.add_favorite, name='add_favorite'),
  path('profile/<int:user_id>/delete_favorite/<int:animal_id>', views.delete_favorite, name='delete_favorite'),
  
]