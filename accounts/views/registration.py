from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from ..forms import SubscriberForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from django.db import transaction
import logging
import requests
from django.core.cache import cache
import dns.resolver
from ..utils import generate_verification_token, get_client_ip
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from ..models import RegistrationToken
import os
import hashlib

logger = logging.getLogger(__name__)

def verify_recaptcha(token):
    """验证 reCAPTCHA token"""
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': token
        })
        result = response.json()
        
        logger.info(f"reCAPTCHA response: {result}")
        
        if result['success']:
            score = float(result.get('score', 0))
            logger.info(f"reCAPTCHA score: {score}")
            
            if score < float(settings.RECAPTCHA_SCORE_THRESHOLD):
                logger.warning(f"Suspicious activity detected. Score: {score}")
                return False
                
            return True
        return False
    except Exception as e:
        logger.error(f"reCAPTCHA verification failed: {str(e)}")
        return False

def verify_email_domain(email):
    """验证邮箱域名是否有效"""
    try:
        domain = email.split('@')[1]
        logger.info(f"Verifying domain: {domain}")
        mx_records = dns.resolver.resolve(domain, 'MX')
        logger.info(f"Found MX records for {domain}: {[str(r.exchange) for r in mx_records]}")
        if not list(mx_records):
            logger.warning(f"No MX records found for {domain}")
            return False
        return True
    except Exception as e:
        logger.error(f"DNS query failed for {email}: {str(e)}")
        return False

def register(request):
    if request.method == 'POST':
        client_ip = get_client_ip(request)
        submission_key = f'registration_attempt_{client_ip}'
        attempt_count = cache.get(submission_key, 0)
        
        if attempt_count >= settings.IP_RATE_LIMIT_MAX:
            messages.error(request, "Too many attempts. Please try again later.")
            return redirect('accounts:register')
        
        cache.set(submission_key, attempt_count + 1, settings.IP_RATE_LIMIT_TIMEOUT)
        device_fingerprint = request.POST.get('device_fingerprint', '')
        device_key = f'device_attempt_{device_fingerprint}'
        device_attempts = cache.get(device_key, 0)
        
        if device_attempts >= settings.DEVICE_RATE_LIMIT_MAX:
            messages.error(request, "Registration limit exceeded. Please try again tomorrow.")
            return redirect('accounts:register')
        
        cache.set(device_key, device_attempts + 1, settings.DEVICE_RATE_LIMIT_TIMEOUT)
        form = SubscriberForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            if not verify_email_domain(email):
                messages.error(request, "Registration failed. Please try again with a different email address.")
                return redirect('accounts:register')
            
            recaptcha_token = request.POST.get('recaptcha_token')
            if not verify_recaptcha(recaptcha_token):
                messages.error(request, "Registration failed. Please try again.")
                return redirect('accounts:register')
            
            try:
                with transaction.atomic():
                    subscriber = form.save(commit=False)
                    subscriber.email = form.cleaned_data['email']
                    subscriber.ip_address = client_ip
                    
                    user = User.objects.create(
                        username=subscriber.email,
                        email=subscriber.email,
                        is_active=False
                    )
                    subscriber.user = user
                    subscriber.credit = 50.00
                    subscriber.save()
                    
                    token = generate_verification_token(subscriber)
                    verification_url = f"{settings.PROTOCOL}://{request.get_host()}/complete-registration/{token.token}/"
                    
                    html_message = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <p>Thank you for subscribing to Appliances 4 Less Doraville Store!</p>
                        
                        <p>Please click the link below to complete your registration and get your ${subscriber.credit} coupon:</p>
                        <p><a href="{verification_url}">Complete Registration</a></p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <img src="cid:coupon_image" alt="${subscriber.credit} Coupon" style="max-width: 100%; height: auto;">
                        </div>
                        
                        <p>Simply show this email when you visit our store at:<br>
                        <strong>6930 Buford Hwy Suite B, Doraville, GA 30340</strong></p>
                        
                        <h3 style="color: #FD742D;">Our business hours:</h3>
                        <ul style="list-style: none; padding-left: 0;">
                            <li>Mon - Thu: 10:00 AM - 6:00 PM</li>
                            <li>Fri - Sat: 10:00 AM - 7:00 PM</li>
                            <li>Sun: Closed</li>
                        </ul>
                        
                        <p style="color: #FD742D; font-weight: bold;">Terms and Conditions:</p>
                        <ul style="list-style: none; padding-left: 0;">
                            <li>• Minimum purchase of $500</li>
                            <li>• Service fee not included</li>
                            <li>• Valid for 180 days from today</li>
                        </ul>
                        
                        <p>We look forward to serving you!</p>
                        
                        <p>Best regards,<br>
                        Appliances 4 Less Team</p>
                    </body>
                    </html>
                    """
                    
                    email = EmailMultiAlternatives(
                        'Welcome to Appliances 4 Less - Complete Your Registration',
                        'This is a plain text message',
                        settings.DEFAULT_FROM_EMAIL,
                        [subscriber.email]
                    )

                    with open('accounts/static/accounts/images/email/coupon.png', 'rb') as f:
                        image = MIMEImage(f.read())
                        image.add_header('Content-ID', '<coupon_image>')
                        email.attach(image)

                    email.attach_alternative(html_message, "text/html")
                    email.mixed_subtype = 'related'
                    
                    try:
                        email.send()
                    except Exception as e:
                        logger.error(f"Email sending failed: {str(e)}")
                        
                    return redirect('accounts:register_success')
                    
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                messages.error(request, "Registration failed. Please try again.")
                return redirect('accounts:register')
        else:
            # 将表单错误转换为messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('accounts:register')
    else:
        form = SubscriberForm()
    
    context = {
        'form': form,
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }
    return render(request, 'accounts/register.html', context)

def register_success(request):
    return render(request, 'accounts/register_success.html')

def complete_registration(request, token):
    """完成注册流程"""
    registration_token = get_object_or_404(RegistrationToken, token=token)
    
    if not registration_token.is_valid():
        messages.error(request, "This verification link has expired or is invalid.")
        return redirect('accounts:register')
    
    subscriber = registration_token.subscriber  # 只获取一次subscriber实例
    
    # 获取临时头像路径
    temp_avatar = request.GET.get('temp_avatar')  # 从URL参数获取临时文件名
    temp_avatar_url = None
    if temp_avatar:
        temp_path = os.path.join('temp', 'uploads', temp_avatar)
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, temp_path)):
            temp_avatar_url = f"{settings.MEDIA_URL}{temp_path}"
    
    # 准备基础上下文数据
    context = {
        'token_valid': True,
        'email': subscriber.email,
        'token': token,
        'temp_avatar_url': temp_avatar_url,
        'subscriber': subscriber
    }
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 表单验证
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/complete_registration.html', context)
        
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'accounts/complete_registration.html', context)
        
        # 验证姓名
        if not first_name or not last_name:
            messages.error(request, "First name and last name are required.")
            return render(request, 'accounts/complete_registration.html', context)

        try:
            with transaction.atomic():
                user = subscriber.user
                
                # 保存用户信息
                user.set_password(password1)
                user.is_active = True
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                
                # 更新订阅者信息
                subscriber.phone = phone
                
                # 处理临时头像文件
                if temp_avatar:
                    temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'uploads', temp_avatar)
                    if os.path.exists(temp_path):
                        final_filename = temp_avatar
                        final_path = os.path.join(settings.MEDIA_ROOT, 'avatars', final_filename)
                        
                        # 移动文件
                        os.makedirs(os.path.dirname(final_path), exist_ok=True)
                        os.rename(temp_path, final_path)
                        subscriber.avatar = f"avatars/{final_filename}"
                
                subscriber.save()
                
                # 更新token状态
                registration_token.is_used = True
                registration_token.is_valid = False
                registration_token.save()
                
                messages.success(request, "Registration completed successfully!")
                return redirect('accounts:registration_verified')
                
        except Exception as e:
            logger.error(f"Registration completion failed: {str(e)}")
            messages.error(request, "Registration failed. Please try again.")
            return render(request, 'accounts/complete_registration.html', context)
    
    return render(request, 'accounts/complete_registration.html', context)

def registration_verified(request):
    """显示注册验证成功页面"""
    return render(request, 'accounts/registration_verified.html') 