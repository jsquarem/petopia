from django.urls import path
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('about/', views.about, name='about'),
  path('lobby/', views.lobby, name='lobby'),
  path('accounts/signup/', views.signup, name='signup'),
  path('animals/', views.animals_index, name='animals.index'),
  path('animals/<int:animal_id>/', views.animals_detail, name='animals.detail'),
  path('profiles/<int:user_id>/', views.profiles_detail, name ='detail'),
  path('profiles/create/', views.ProfileCreate.as_view(), name='profiles_create'),
  path('profiles/<int:pk>/update/', views.ProfileUpdate.as_view(), name='profiles_update'),
  path('profiles/<int:pk>/delete/', views.ProfileDelete.as_view(), name='profiles_delete'),
  path('organizations/', views.organizations_index, name='organizations.index'),
  path('organizations/<str:organization_id>/', views.organizations_detail, name='organizations.detail'),
  path('profile/<int:user_id>/add_photo/', views.add_photo, name='add_photo'),
  path('profile/<int:user_id>/add_favorite/<int:animal_id>', views.add_favorite, name='add_favorite'),
  path('profile/<int:user_id>/delete_favorite/<int:animal_id>', views.delete_favorite, name='delete_favorite'),
]