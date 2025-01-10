from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Subscriber, RegistrationToken

class SubscriberInline(admin.StackedInline):
    model = Subscriber
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (SubscriberInline,)
    list_display = (
        'username', 
        'first_name',
        'last_name',
        'email', 
        'get_phone',
        'is_active', 
        'date_joined', 
        'get_ip_address',
        'get_token',
        'get_token_used',
        'get_token_valid'
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
    
    def get_phone(self, obj):
        return obj.subscriber.phone if hasattr(obj, 'subscriber') else '-'
    get_phone.short_description = 'Phone'
    
    def get_ip_address(self, obj):
        return obj.subscriber.ip_address if hasattr(obj, 'subscriber') else '-'
    get_ip_address.short_description = 'IP Address'
    
    def get_token(self, obj):
        if hasattr(obj, 'subscriber') and hasattr(obj.subscriber, 'registrationtoken'):
            return obj.subscriber.registrationtoken.token
        return '-'
    get_token.short_description = 'Token'
    
    def get_token_used(self, obj):
        if hasattr(obj, 'subscriber') and hasattr(obj.subscriber, 'registrationtoken'):
            return obj.subscriber.registrationtoken.is_used
        return False
    get_token_used.short_description = 'Token Used'
    get_token_used.boolean = True
    
    def get_token_valid(self, obj):
        if hasattr(obj, 'subscriber') and hasattr(obj.subscriber, 'registrationtoken'):
            return obj.subscriber.registrationtoken.is_valid
        return False
    get_token_valid.short_description = 'Token Valid'
    get_token_valid.boolean = True

class RegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'token', 'created_at', 'is_used', 'is_valid')
    list_filter = ('is_used', 'created_at')
    search_fields = ('subscriber__email', 'token')
    readonly_fields = ('token', 'created_at')

# 重新注册 User 模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(RegistrationToken, RegistrationTokenAdmin) 