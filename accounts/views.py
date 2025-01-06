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

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():  # 添加事务处理
                    subscriber = form.save(commit=False)
                    
                    # 格式化名字：首字母大写，其余小写
                    subscriber.first_name = subscriber.first_name.strip().title()
                    subscriber.last_name = subscriber.last_name.strip().title()
                    
                    user = User.objects.create_user(
                        username=subscriber.email,
                        email=subscriber.email,
                        password=form.cleaned_data['password'],  # 使用表单中的密码
                        first_name=subscriber.first_name,
                        last_name=subscriber.last_name
                    )
                    subscriber.user = user
                    subscriber.save()
                    
                    # 发送确认邮件
                    subject = 'Welcome to Appliances 4 Less - Your $50 Coupon!'
                    html_message = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <h2 style="color: #185A56;">Dear {subscriber.first_name} {subscriber.last_name},</h2>
                        
                        <p>Thank you for subscribing to Appliances 4 Less Doraville Store!</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <img src="cid:coupon_image" alt="$50 Coupon" style="max-width: 100%; height: auto;">
                        </div>
                        
                        <p>Simply show this email when you visit our store at:<br>
                        <strong>6930 Buford Hwy Suite B, Doraville, GA 30340</strong></p>
                        
                        <h3 style="color: #FD742D;">Our business hours:</h3>
                        <ul style="list-style: none; padding-left: 0;">
                            <li>Mon - Tue: 10:00 AM - 7:00 PM</li>
                            <li>Wed - Thu: 10:00 AM - 6:00 PM</li>
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
                    
                    # 使用EmailMultiAlternatives发送邮件
                    email = EmailMultiAlternatives(
                        subject,
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
    
    return render(request, 'accounts/register.html', {'form': form}) 

def register_success(request):
    return render(request, 'accounts/register_success.html') 