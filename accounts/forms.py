from django import forms
from django.contrib.auth.models import User
from .models import Subscriber

class SubscriberForm(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # 检查User表中是否存在此email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
            
        # 检查Subscriber表中是否存在此email
        if Subscriber.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
            
        return email

    class Meta:
        model = Subscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Enter your email'
            })
        } 