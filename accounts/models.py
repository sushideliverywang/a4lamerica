from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import hashlib
import os

class Subscriber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, unique=True, verbose_name='Email')
    phone = models.CharField(max_length=10, null=True, blank=True, verbose_name='Phone Number')
    phone_verified = models.BooleanField(default=False, verbose_name='Phone Number Verified')
    credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Available credit balance (includes coupons and refunds)",
        verbose_name='Credit Balance'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Avatar',
        help_text='User profile picture (2x2 inch)'
    )

    def __str__(self):
        return self.email

    @property
    def is_verified(self):
        """通过 user.is_active 判断是否完成验证"""
        return self.user.is_active

    def get_avatar_url(self):
        """返回用户头像URL，如果没有则返回默认头像"""
        if self.avatar:
            return self.avatar.url
        return f"{settings.MEDIA_URL}avatars/default.png"

    def generate_filename(self):
        """根据用户邮箱生成唯一的文件名"""
        email_hash = hashlib.md5(self.email.encode()).hexdigest()
        return f"{email_hash}.png"

    def save(self, *args, **kwargs):
        # 如果有新的头像文件上传
        if self.avatar:
            # 生成新的文件名
            new_name = f"avatars/{self.generate_filename()}"
            # 如果文件名不同，重命名文件
            if self.avatar.name != new_name:
                # 如果存在旧文件，删除它
                if os.path.isfile(self.avatar.path):
                    os.remove(self.avatar.path)
                # 设置新的文件名
                self.avatar.name = new_name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'
        ordering = ['-created_at']

class RegistrationToken(models.Model):
    subscriber = models.OneToOneField(
        'Subscriber',
        on_delete=models.CASCADE,
        related_name='registration_token'
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """检查token是否在24小时内有效"""
        return not self.is_used and self.created_at > timezone.now() - timedelta(hours=24)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]
        
    def __str__(self):
        return f"Token for {self.subscriber.email} ({'used' if self.is_used else 'unused'})"

