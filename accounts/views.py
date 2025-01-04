from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SubscriberForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from pathlib import Path

def register(request):
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            subscriber = form.save(commit=False)
            
            # 格式化名字：首字母大写，其余小写
            subscriber.first_name = subscriber.first_name.strip().title()
            subscriber.last_name = subscriber.last_name.strip().title()
            
            user = User.objects.create_user(
                username=subscriber.email,
                email=subscriber.email,
                password=None,
                first_name=subscriber.first_name,  # 使用已格式化的名字
                last_name=subscriber.last_name     # 使用已格式化的名字
            )
            subscriber.user = user
            subscriber.save()
            
            # 发送确认邮件
            subject = 'Welcome to Appliances 4 Less - Your $50 Discount Coupon!'
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #185A56;">Dear {subscriber.first_name},</h2>
                
                <p>Thank you for subscribing to Appliances 4 Less Doraville Store!</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <img src="cid:coupon_image" alt="$50 Discount Coupon" style="max-width: 100%; height: auto;">
                </div>
                
                <p>Simply show this email when you visit our store at:<br>
                <strong>6930 Buford Hwy Suite B, Doraville, GA 30340</strong></p>
                
                <h3 style="color: #FD742D;">Our business hours:</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li>Mon - Tue: 10:00 AM - 7:00 PM</li>
                    <li>Wed - Thu: 10:00 AM - 6:00 PM</li>
                    <li>Fri - Sat: 10:00 AM - 5:00 PM</li>
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
            
            email.send()
            return redirect('register_success')  # 假设您的URL name是'register'
    else:
        form = SubscriberForm()
    
    return render(request, 'accounts/register.html', {'form': form}) 

def register_success(request):
    return render(request, 'accounts/register_success.html') 