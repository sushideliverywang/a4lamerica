from django.urls import path
from . import views

app_name = 'photo_crop'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_photo, name='upload'),
    path('crop/', views.crop_photo, name='crop'),
]
