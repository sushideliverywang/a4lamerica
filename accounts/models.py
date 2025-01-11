from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

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

    def __str__(self):
        return self.email

    @property
    def is_verified(self):
        """通过 user.is_active 判断是否完成验证"""
        return self.user.is_active

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

