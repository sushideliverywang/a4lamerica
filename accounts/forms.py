from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
# 注释掉 organization 依赖
# from organization.models import Company
from django.contrib.auth.password_validation import validate_password
import re


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

    def clean_phone(self):
        """清理和验证电话号码

        去除所有非数字字符（括号、破折号、空格、点等）
        支持带国家码+1的格式（自动去除）
        验证剩余数字是否为10位（美国电话号码标准）
        返回纯数字格式的电话号码
        """
        phone = self.cleaned_data.get('phone', '')

        # 去除所有非数字字符
        digits_only = re.sub(r'\D', '', phone)

        # 如果是11位且以1开头（美国国家码），去除开头的1
        if len(digits_only) == 11 and digits_only.startswith('1'):
            digits_only = digits_only[1:]

        # 验证是否为10位数字（美国电话号码）
        if len(digits_only) != 10:
            raise ValidationError(
                f"Phone number must be exactly 10 digits. You entered {len(digits_only)} digits."
            )

        # 验证是否全部是数字
        if not digits_only.isdigit():
            raise ValidationError("Phone number must contain only digits")

        # 返回纯数字格式（10位）
        return digits_only

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
