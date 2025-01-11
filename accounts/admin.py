from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Subscriber, RegistrationToken
import logging

logger = logging.getLogger('accounts')

class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 
        'first_name',
        'last_name',
        'email', 
        'get_phone',    
        'get_phone_verified',
        'is_active', 
        'date_joined', 
        'get_ip_address',
        'get_token_used',
        'get_token_valid',
    
    )
    list_filter = ('is_active', 'date_joined')
    search_fields = (
        'username', 
        'email', 
        'first_name',
        'last_name',
        'subscriber__phone',
        'subscriber__ip_address'
    )
    ordering = ('-date_joined',)
    sortable_by = ('username', 'email', 'date_joined', 'is_active')
    
    def get_phone_verified(self, obj):
        return obj.subscriber.phone_verified if hasattr(obj, 'subscriber') else False
    get_phone_verified.short_description = 'Phone Verified'
    get_phone_verified.boolean = True
    
    def get_phone(self, obj):
        return obj.subscriber.phone if hasattr(obj, 'subscriber') else '-'
    get_phone.short_description = 'Phone'
    
    def get_ip_address(self, obj):
        return obj.subscriber.ip_address if hasattr(obj, 'subscriber') else '-'
    get_ip_address.short_description = 'IP Address'
    
    def get_token_used(self, obj):
        tokens = RegistrationToken.objects.filter(subscriber__user=obj)
        return tokens.first().is_used if tokens.exists() else False
    get_token_used.short_description = 'Token Used'
    get_token_used.boolean = True
    
    def get_token_valid(self, obj):
        tokens = RegistrationToken.objects.filter(subscriber__user=obj)
        return tokens.first().is_valid() if tokens.exists() else False
    get_token_valid.short_description = 'Token Valid'
    get_token_valid.boolean = True

# 只注册 User 模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin) 