import hashlib
import time
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import RegistrationToken
import logging

logger = logging.getLogger('accounts')

def generate_verification_token(subscriber):
    """
    为订阅者生成唯一的验证token
    """
    # 组合唯一标识符
    unique_string = f"{subscriber.email}{time.time()}{uuid.uuid4()}"
    # 生成 SHA-256 哈希
    token = hashlib.sha256(unique_string.encode()).hexdigest()
    
    # 创建或更新 RegistrationToken
    registration_token, created = RegistrationToken.objects.update_or_create(
        subscriber=subscriber,
        defaults={
            'token': token,
            'is_used': False
        }
    )
    
    return registration_token

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    remote_addr = request.META.get('REMOTE_ADDR')
    
    # 添加调试日志
    logger.debug("DEBUG: META headers:")
    logger.debug(f"X-Forwarded-For: {x_forwarded_for}")
    logger.debug(f"X-Real-IP: {x_real_ip}")
    logger.debug(f"REMOTE_ADDR: {remote_addr}")
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = x_real_ip or remote_addr
    
    logger.debug(f"Final IP: {ip}")
    return ip
