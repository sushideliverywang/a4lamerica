"""
工具函数 - 为 frontend app 提供必要的工具函数
"""

import hashlib
import hmac
from django.conf import settings

def get_item_hash(item):
    """
    生成商品哈希编码
    """
    if not item or not hasattr(item, 'id'):
        return None
    
    # 使用商品ID和密钥生成哈希
    message = f"item_{item.id}"
    secret_key = getattr(settings, 'ITEM_HASH_SECRET_KEY', 'default-secret-key')
    
    # 使用HMAC生成哈希
    hash_obj = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    
    return hash_obj.hexdigest()

def encode_item_id(item):
    """
    编码商品ID为哈希
    """
    return get_item_hash(item)

def decode_item_id(item_hash):
    """
    解码商品哈希获取商品对象
    通过遍历所有商品来找到匹配的哈希
    """
    if not item_hash:
        return None
    
    try:
        from .models_proxy import InventoryItem
        
        # 遍历所有已发布的商品，找到匹配的哈希
        items = InventoryItem.objects.filter(
            published=True,
            current_state_id__in=[4, 5, 8]  # 只查找可销售状态的商品
        )
        
        for item in items:
            if get_item_hash(item) == item_hash:
                return item
        
        # 如果找不到匹配的商品，返回None
        return None
        
    except Exception:
        return None

def generate_order_number(location):
    """
    生成订单编号
    """
    from django.utils import timezone
    import uuid
    
    # 生成基于时间戳和随机数的订单编号
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"{location.slug.upper()}-{timestamp}-{random_suffix}"