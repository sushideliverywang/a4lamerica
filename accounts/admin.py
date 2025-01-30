from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Subscriber, RegistrationToken
from django.utils.html import format_html
import logging
import os
from django.conf import settings

logger = logging.getLogger('accounts')

class CustomUserAdmin(UserAdmin):
    list_display = (
        'get_avatar',
        'username', 
        'first_name',
        'last_name',
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
        'first_name',
        'last_name',
        'subscriber__phone',
        'subscriber__ip_address'
    )
    ordering = ('-date_joined',)
    sortable_by = ('username', 'date_joined', 'is_active')
    
    def get_avatar(self, obj):
        if hasattr(obj, 'subscriber') and obj.subscriber.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.subscriber.avatar.url
            )
        return format_html(
            '<img src="/static/accounts/images/default-avatar.png" width="50" height="50" style="border-radius: 50%;" />'
        )
    get_avatar.short_description = 'Avatar'
    
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

    def delete_model(self, request, obj):
        """
        处理单个对象删除
        """
        try:
            # 获取关联的subscriber
            if hasattr(obj, 'subscriber'):
                subscriber = obj.subscriber
                
                # 删除头像文件
                if subscriber.avatar:
                    avatar_path = os.path.join(settings.MEDIA_ROOT, str(subscriber.avatar))
                    if os.path.exists(avatar_path):
                        os.remove(avatar_path)
                        logger.info(f"Deleted avatar file: {avatar_path}")
                
                # 删除相关的token
                tokens = RegistrationToken.objects.filter(subscriber=subscriber)
                for token in tokens:
                    token.delete()
                    logger.info(f"Deleted token: {token.token}")
                
                # 删除subscriber
                subscriber.delete()
                logger.info(f"Deleted subscriber: {subscriber.email}")
            
            # 删除用户
            obj.delete()
            logger.info(f"Deleted user: {obj.username}")
            
        except Exception as e:
            logger.error(f"Error deleting user {obj.username}: {str(e)}")
            raise

    def delete_queryset(self, request, queryset):
        """
        处理批量删除
        """
        for obj in queryset:
            self.delete_model(request, obj)

# 注销默认的User admin并注册自定义的admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin) 