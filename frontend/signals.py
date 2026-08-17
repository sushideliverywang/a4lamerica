"""
Frontend app 信号处理
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart_utils import merge_session_cart_to_user
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    用户登录时，将session购物车合并到数据库购物车
    """
    if hasattr(user, 'customer'):
        added_count, skipped_count = merge_session_cart_to_user(request, user.customer)

        # 可选：将合并结果存储到session中，用于显示消息
        if added_count > 0:
            request.session['cart_merge_message'] = f'{added_count} items added to your cart'
            logger.info(f"Cart merged for user {user.username}: {added_count} added, {skipped_count} skipped")
