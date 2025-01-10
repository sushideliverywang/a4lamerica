from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SubscriberForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from pathlib import Path
from django.core.exceptions import ValidationError
from django.db import transaction
import logging
import requests  # 新增
from django.core.cache import cache
import dns.resolver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .utils import generate_verification_token, get_client_ip
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from .models import RegistrationToken

logger = logging.getLogger(__name__)

def verify_recaptcha(token):
    """验证 reCAPTCHA token"""
    try:
        # 向 Google 验证服务器发送请求
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': token
        })
        result = response.json()
        
        # 添加详细日志
        logger.info(f"reCAPTCHA response: {result}")
        
        if result['success']:
            score = float(result.get('score', 0))
            logger.info(f"reCAPTCHA score: {score}")
            
            # 调整验证逻辑
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
        # 获取域名部分
        domain = email.split('@')[1]
        
        # 添加详细日志
        logger.info(f"Verifying domain: {domain}")
        
        # 查询域名的 MX 记录
        mx_records = dns.resolver.resolve(domain, 'MX')
        
        # 记录找到的 MX 记录
        logger.info(f"Found MX records for {domain}: {[str(r.exchange) for r in mx_records]}")
        
        # 确保至少有一个 MX 记录
        if not list(mx_records):
            logger.warning(f"No MX records found for {domain}")
            return False
            
        return True
        
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, 
            IndexError) as e:  # 移除了 SERVFAIL
        # 只记录日志，不返回具体错误信息
        logger.warning(f"Invalid email domain for {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"DNS query failed for {email}: {str(e)}")
        return False

def register(request):
    if request.method == 'POST':
        # 获取客户端IP
        client_ip = request.META.get('REMOTE_ADDR')
        
        # 检查提交频率
        submission_key = f'registration_attempt_{client_ip}'
        attempt_count = cache.get(submission_key, 0)
        
        if attempt_count >= settings.IP_RATE_LIMIT_MAX:
            messages.error(request, "Too many attempts. Please try again later.")
            return redirect('register')
            
        # 增加尝试计数
        cache.set(submission_key, attempt_count + 1, settings.IP_RATE_LIMIT_TIMEOUT)
        
        # 获取设备指纹
        device_fingerprint = request.POST.get('device_fingerprint', '')
        
        # 检查设备限制
        device_key = f'device_attempt_{device_fingerprint}'
        device_attempts = cache.get(device_key, 0)
        
        if device_attempts >= settings.DEVICE_RATE_LIMIT_MAX:
            messages.error(request, "Registration limit exceeded. Please try again tomorrow.")
            return redirect('register')
            
        # 增加设备尝试计数
        cache.set(device_key, device_attempts + 1, settings.DEVICE_RATE_LIMIT_TIMEOUT)
        
        form = SubscriberForm(request.POST)
        
        # 检查蜜罐字段
        honeypot_fields = ['first_name', 'last_name', 'phone']
        for field in honeypot_fields:
            if request.POST.get(field):  # 如果蜜罐字段有值
                logger.warning(f"Honeypot triggered: {field} field was filled. IP: {get_client_ip(request)}")
                messages.error(request, "Registration failed. Please try again later.")
                return redirect('register')
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # 验证邮箱域名，使用通用错误消息
            if not verify_email_domain(email):
                messages.error(request, "Registration failed. Please try again with a different email address.")
                return redirect('register')
            
            # reCAPTCHA 验证，使用通用错误消息
            recaptcha_token = request.POST.get('recaptcha_token')
            if not verify_recaptcha(recaptcha_token):
                messages.error(request, "Registration failed. Please try again.")
                return redirect('register')
            
            try:
                with transaction.atomic():
                    subscriber = form.save(commit=False)
                    subscriber.email = form.cleaned_data['email']
                    subscriber.ip_address = client_ip  # 记录IP地址
                    
                    # 创建用户
                    user = User.objects.create(
                        username=subscriber.email,
                        email=subscriber.email,
                        is_active=False  # 设置为未激活状态
                    )
                    subscriber.user = user
                    
                    subscriber.credit = 50.00  # 新用户默认 $50 优惠券
                    
                    subscriber.save()
                    
                    # 生成验证token
                    token = generate_verification_token(subscriber)
                    verification_url = f"{settings.PROTOCOL}://{request.get_host()}/complete-registration/{token.token}/"
                    
                    # 保持现有的邮件模板
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
                    
                    # 使用 EmailMultiAlternatives 发送邮件
                    email = EmailMultiAlternatives(
                        'Welcome to Appliances 4 Less - Complete Your Registration',
                        'This is a plain text message',
                        settings.DEFAULT_FROM_EMAIL,
                        [subscriber.email]
                    )

                    # 读取优惠券图片
                    with open('accounts/static/accounts/images/email/coupon.png', 'rb') as f:
                        image = MIMEImage(f.read())
                        image.add_header('Content-ID', '<coupon_image>')
                        email.attach(image)

                    # 添加HTML内容（确保在添加图片后添加HTML内容）
                    email.attach_alternative(html_message, "text/html")
                    email.mixed_subtype = 'related'
                    
                    try:
                        email.send()
                    except Exception as e:
                        # 记录邮件发送错误但不中断注册流程
                        logger.error(f"Email sending failed: {str(e)}")
                        
                    return redirect('register_success')
                    
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                messages.error(request, "Registration failed. Please try again.")
                return redirect('register')
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
    # 获取token记录
    registration_token = get_object_or_404(RegistrationToken, token=token)
    
    # 检查token是否有效
    if not registration_token.is_valid():
        messages.error(request, "This verification link has expired or is invalid.")
        return redirect('register')
    
    # 获取关联的subscriber
    subscriber = registration_token.subscriber
    
    if request.method == 'POST':
        # 验证密码
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/complete_registration.html', {
                'token_valid': True,
                'email': subscriber.email
            })
        
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'accounts/complete_registration.html', {
                'token_valid': True,
                'email': subscriber.email
            })
        
        try:
            with transaction.atomic():
                # 更新用户信息
                user = subscriber.user
                user.password = make_password(password1)
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.is_active = True
                user.save()
                
                # 处理电话号码 - 只保留数字
                phone = request.POST.get('phone', '')
                phone_digits = ''.join(filter(str.isdigit, phone))  # 移除所有非数字字符
                
                # 更新 subscriber 信息
                subscriber.phone = phone_digits
                subscriber.save()
                
                # 标记token为已使用
                registration_token.is_used = True
                registration_token.save()
                
                messages.success(request, "Registration completed successfully!")
                return redirect('registration_verified')
                
        except Exception as e:
            logger.error(f"Registration completion failed: {str(e)}")
            messages.error(request, "Registration failed. Please try again.")
    
    # GET 请求显示表单
    return render(request, 'accounts/complete_registration.html', {
        'token_valid': registration_token.is_valid(),
        'email': subscriber.email
    })

def registration_verified(request):
    """显示注册验证成功页面"""
    return render(request, 'accounts/registration_verified.html')


