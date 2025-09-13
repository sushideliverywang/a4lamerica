from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
# 注释掉 organization 依赖
# from organization.models import Company
from django.contrib.auth.password_validation import validate_password


User = get_user_model()

class CustomerRegistrationForm(UserCreationForm):
    """客户注册表单"""
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        help_text="Required. Enter a valid phone number."
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        help_text="Required. Enter your first name."
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        help_text="Required. Enter your last name."
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'password1',
            'password2'
        )

    def clean_email(self):
        """检查邮箱是否已被注册"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email

    def clean(self):
        """添加密码匹配验证"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "The two password fields didn't match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # 使用 email 作为 username
        if commit:
            user.save()
        return user
