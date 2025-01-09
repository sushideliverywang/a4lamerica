from django import forms
from .models import Subscriber
import re

class SubscriberForm(forms.ModelForm):
    # 蜜罐字段设置为非必需
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    
    # 保留 email 字段验证
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Subscriber.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email

    class Meta:
        model = Subscriber
        fields = ['email', 'first_name', 'last_name', 'phone']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Enter your email'
            })
        } 