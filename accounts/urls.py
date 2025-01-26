from django.urls import path
from .views import (
    register, register_success, complete_registration,
    registration_verified, crop_avatar, save_avatar
)

app_name = 'accounts'

urlpatterns = [
    path('', register, name='register'),
    path('success/', register_success, name='register_success'),
    path('complete-registration/<str:token>/', complete_registration, name='complete_registration'),
    path('verified/', registration_verified, name='registration_verified'),
    path('avatar/save/<str:token>/', save_avatar, name='save_avatar'),
    path('avatar/crop/<str:token>/', crop_avatar, name='crop_avatar'),
] 