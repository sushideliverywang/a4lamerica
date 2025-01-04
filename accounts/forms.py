from django import forms
from .models import Subscriber
import re

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-colors bg-white/50',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-colors bg-white/50',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-colors bg-white/50',
                'placeholder': 'Enter your email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-colors bg-white/50',
                'placeholder': 'Enter your phone number'
            })
        }
        error_messages = {
            'first_name': {
                'required': 'First name is required',
                'max_length': 'First name is too long'
            },
            'last_name': {
                'required': 'Last name is required',
                'max_length': 'Last name is too long'
            },
            'email': {
                'required': 'Email address is required',
                'invalid': 'Please enter a valid email address'
            },
            'phone': {
                'required': 'Phone number is required'
            }
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError('Phone number is required')
        
        # 移除所有非数字字符
        phone = re.sub(r'\D', '', phone)
        
        # 验证电话号码长度（美国号码为10位）
        if len(phone) != 10:
            raise forms.ValidationError('Please enter a valid 10-digit phone number')
        
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Subscriber.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError('First name should only contain letters')
        return first_name.strip()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError('Last name should only contain letters')
        return last_name.strip() 