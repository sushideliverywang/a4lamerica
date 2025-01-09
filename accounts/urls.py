from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('success/', views.register_success, name='register_success'),
    path('complete-registration/<str:token>/', views.complete_registration, name='complete_registration'),
    path('verified/', views.registration_verified, name='registration_verified'),
] 