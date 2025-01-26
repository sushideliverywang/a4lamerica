from django.utils import timezone
from datetime import timedelta
import os
import logging
from django.conf import settings
from .models import RegistrationToken, Subscriber
import hashlib

logger = logging.getLogger(__name__)

def cleanup_expired_registrations():
    """清理过期的注册数据和临时文件"""
    try:
        # 获取所有token
        # 只获取未使用的token且用户未激活的记录
        tokens = RegistrationToken.objects.filter(
            is_used=False,
            subscriber__user__is_active=False
        )
        expired_tokens = [token for token in tokens if not token.is_valid()]
        
        for token in expired_tokens:
            try:
                # 使用subscriber的方法生成文件名
                temp_avatar = token.subscriber.generate_filename()
                
                # 删除临时头像文件
                temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'uploads', temp_avatar)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"Deleted temp avatar: {temp_path}")
                
                # 删除subscriber（会级联删除token）
                subscriber = token.subscriber
                user = subscriber.user
                
                # 再次确认用户未激活
                if not user.is_active:
                    # 按顺序删除关联数据
                    token.delete()
                    logger.info(f"Deleted expired token: {token.token}")
                    
                    subscriber.delete()
                    logger.info(f"Deleted expired registration: {subscriber.email}")
                    
                    user.delete()
                    logger.info(f"Deleted user: {user.username}")
                else:
                    logger.warning(f"Skipped deletion for active user: {user.username}")
                
            except Exception as e:
                logger.error(f"Error cleaning up token {token.token}: {str(e)}")
                continue
        
        logger.info(f"Cleanup completed. Processed {len(expired_tokens)} expired registrations")
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}") 