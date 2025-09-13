import logging
logger = logging.getLogger('accounts')

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import CustomerRegistrationForm
from .models import User, Customer
from django.utils import timezone
from django.http import Http404
from django.views.generic import ListView
from django.contrib.admin.models import LogEntry

from django.db.models import Q
import json
from django.core.paginator import Paginator
from .utils import get_client_ip, verify_recaptcha, verify_email_domain, check_ip_registration_limit
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

def register_customer(request):
    """客户注册视图函数
    处理客户注册表单提交和账户创建
    """
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # 获取并检查 IP
                ip_address = get_client_ip(request)
                if not check_ip_registration_limit(ip_address):
                    messages.error(request, 'Too many registration attempts. Please try again later.')
                    return render(request, 'accounts/register_customer.html', {'form': form})
                
                # 获取 reCAPTCHA token
                recaptcha_token = request.POST.get('g-recaptcha-response')
                email = form.cleaned_data['email']
                
                # 执行安全检查
                if not all([
                    verify_recaptcha(recaptcha_token),
                    verify_email_domain(email)
                ]):
                    messages.error(request, 'Verification failed. Please try again.')
                    return render(request, 'accounts/register_customer.html', {'form': form})

                with transaction.atomic():
                    # 创建用户账户，但设置为未激活
                    user = form.save(commit=False)
                    user.is_staff = False
                    user.is_active = False  # 设置为未激活
                    user.save()
                    
                    # 创建客户档案
                    customer = Customer.objects.create(
                        user=user,
                        phone=form.cleaned_data['phone'],
                        email=form.cleaned_data['email'],
                        ip_address=get_client_ip(request)
                    )
                    
                    # 生成激活令牌
                    activation_token = customer.generate_activation_token()
                    
                    # 发送激活邮件
                    activation_link = request.build_absolute_uri(
                        reverse('accounts:activate_customer', args=[str(activation_token)])
                    )
                    
                    context = {
                        'user': user,
                        'activation_link': activation_link,
                        'expiry_hours': 24,
                    }
                    
                    html_message = render_to_string('accounts/email/activation_email.html', context)
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        'Activate Your Account',
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.success(
                        request, 
                        'Registration successful! Please check your email to activate your account.'
                    )
                    return render(request, 'accounts/registration_success.html', {
                        'email': user.email
                    })
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'Registration failed. Please try again.')
                return render(request, 'accounts/register_customer.html', {'form': form})
        
        # 表单验证失败时显示具体错误
        for field, errors in form.errors.items():
            for error in errors:
                if field == 'password2' and "didn't match" in error:
                    messages.error(request, "The passwords don't match. Please try again.")
                else:
                    messages.error(request, f"{error}")
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'accounts/register_customer.html', {
        'form': form,
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY,
    })
    

@login_required
def logout_view(request):
    logout(request)
        # 添加登出成功消息
    messages.success(request, 'You have been successfully logged out.')
    return redirect('frontend:home')
    
    
    
@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Your old password was entered incorrectly.')
            return render(request, 'accounts/change_password.html')
            
        if new_password1 != new_password2:
            messages.error(request, 'The two password fields didn\'t match.')
            return render(request, 'accounts/change_password.html')
            
        request.user.set_password(new_password1)
        request.user.save()
        update_session_auth_hash(request, request.user)  # 保持用户登录状态
        messages.success(request, 'Your password was successfully updated!')
        

        return redirect('frontend:home')
        
    return render(request, 'accounts/change_password.html')

def login_view(request):
    """
    统一的登录视图
    - 根据用户类型自动重定向到相应页面
    - 使用模糊的错误消息提高安全性
    - 检查用户账户状态
    """
    # 获取next参数（从GET或POST请求中）
    next_url = request.GET.get('next') or request.POST.get('next')
    
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'accounts/login.html', {'next': next_url})
            
        try:
            # 先获取用户对象
            user = User.objects.get(email=email)
            
            # 检查账户状态
            if not user.is_active:
                if hasattr(user, 'customer'):
                    if not user.customer.is_email_verified:
                        messages.error(request, 'Please activate your account. Check your email for the activation link.')
                    else:
                        messages.error(request, 'This account has been deactivated. Please contact support.')
                elif hasattr(user, 'staff'):
                    if user.staff.registration_token:
                        messages.error(request, 'Please complete your registration. Check your email for the registration link.')
                    else:
                        messages.error(request, 'Your account has been deactivated. Please contact your administrator.')
                else:
                    messages.error(request, 'This account has been deactivated. Please contact support.')
                return render(request, 'accounts/login.html', {'next': next_url})
            
            # 验证密码
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
                # 只有普通客户才使用next_url，员工和管理员直接重定向到dashboard
                if not user.is_staff and next_url:
                    return redirect(next_url)
                return redirect('frontend:home')
            else:
                messages.error(request, 'Invalid email or password.')
                
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html', {'next': next_url})

    
def activate_customer(request, token):
    try:
        customer = Customer.objects.get(
            activation_token=token,
            token_expiry__gt=timezone.now(),
            is_email_verified=False
        )
        
        with transaction.atomic():
            # 激活用户
            customer.user.is_active = True
            customer.user.save()
            
            # 更新客户状态
            customer.is_email_verified = True
            customer.activation_token = None
            customer.token_expiry = None
            customer.save()
            
            # 自动登录用户
            login(request, customer.user)
            
            messages.success(request, 'Your account has been successfully activated!')
            return redirect('frontend:home')
            
    except Customer.DoesNotExist:
        messages.error(request, 'Invalid or expired activation link.')
        return redirect('accounts:login')