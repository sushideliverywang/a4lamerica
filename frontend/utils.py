"""
工具函数 - 为 frontend app 提供必要的工具函数
"""

import hashlib
import hmac
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def is_valid_hash(encoded_id):
    """
    验证哈希字符串是否有效（只包含十六进制字符）

    Args:
        encoded_id (str): 待验证的哈希字符串

    Returns:
        bool: 如果有效返回True，否则返回False
    """
    if not encoded_id or not isinstance(encoded_id, str):
        return False

    # SHA256生成的哈希长度应该是64位十六进制字符
    if len(encoded_id) != 64:
        return False

    # 只允许十六进制字符（0-9, a-f, A-F）
    return bool(re.match(r'^[0-9a-fA-F]{64}$', encoded_id))


def sanitize_hash_for_cache_key(encoded_id):
    """
    清理哈希字符串用于缓存键，防止特殊字符导致问题

    Args:
        encoded_id (str): 原始哈希字符串

    Returns:
        str: 清理后的哈希字符串（只包含小写十六进制字符）
    """
    # 只保留十六进制字符并转换为小写
    return ''.join(c.lower() for c in encoded_id if c in '0123456789abcdefABCDEF')[:64]


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
    # 安全检查1：验证输入格式
    if not is_valid_hash(item_hash):
        # 记录可疑的输入（可能是攻击）
        logger.warning(f"Invalid hash format detected: {item_hash[:100]}")
        return None

    try:
        from .models_proxy import InventoryItem

        # 遍历所有商品，找到匹配的哈希（移除限制以支持已售商品访问）
        items = InventoryItem.objects.all()

        for item in items:
            if get_item_hash(item) == item_hash:
                return item

        # 如果找不到匹配的商品，返回None
        return None

    except Exception:
        return None



# === SEO工具类 ===

class SEOContentGenerator:
    """SEO内容生成器"""
    
    def __init__(self):
        from .config.seo_keywords import CITIES, SERVICE_TYPES
        self.cities = CITIES
        self.services = SERVICE_TYPES
    
    def generate_page_title(self, city_key, service_key):
        """
        生成页面标题
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            str: 页面标题
        """
        from .config.seo_keywords import get_city_by_slug, get_service_by_key
        city = get_city_by_slug(city_key)
        service = get_service_by_key(service_key)
        
        if not city or not service:
            return "家电服务"
        
        return f"{city['name']} {service['name']}服务 - 专业家电{service['name']} | A4L America"
    
    def generate_meta_description(self, city_key, service_key):
        """
        生成页面描述
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            str: 页面描述
        """
        from .config.seo_keywords import get_city_by_slug, get_service_by_key, get_nearby_cities
        city = get_city_by_slug(city_key)
        service = get_service_by_key(service_key)
        
        if not city or not service:
            return "专业的家电服务提供商"
        
        nearby_cities = get_nearby_cities(city_key)
        # 确保 nearby_cities 是字符串列表
        if nearby_cities and isinstance(nearby_cities[0], dict):
            nearby_city_names = [city['name'] for city in nearby_cities]
        else:
            nearby_city_names = nearby_cities
        nearby_str = "、".join(nearby_city_names[:3]) if nearby_city_names else ""
        
        return f"在{city['name']}及周边地区提供专业的家电{service['name']}服务。服务范围包括{nearby_str}等城市。快速响应，专业安装，让您的家电使用更安心。"
    
    def generate_h1_title(self, city_key, service_key):
        """
        生成H1标题
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            str: H1标题
        """
        from .config.seo_keywords import get_city_by_slug, get_service_by_key
        city = get_city_by_slug(city_key)
        service = get_service_by_key(service_key)
        
        if not city or not service:
            return "家电服务"
        
        return f"{city['name']} {service['name']}服务"
    
    def generate_content_sections(self, city_key, service_key):
        """
        生成页面内容段落
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            dict: 包含各个内容段落的字典
        """
        from .config.seo_keywords import get_city_by_slug, get_service_by_key, get_nearby_cities
        city = get_city_by_slug(city_key)
        service = get_service_by_key(service_key)
        
        if not city or not service:
            return {}
        
        nearby_cities = get_nearby_cities(city_key)
        # 确保 nearby_cities 是字符串列表
        if nearby_cities and isinstance(nearby_cities[0], dict):
            nearby_city_names = [city['name'] for city in nearby_cities]
        else:
            nearby_city_names = nearby_cities
        nearby_str = "、".join(nearby_city_names[:5]) if nearby_city_names else ""
        
        sections = {
            'intro': f"在{city['name']}，我们提供专业的家电{service['name']}服务。无论您需要什么类型的家电{service['name']}，我们的专业团队都能为您提供优质的服务。",
            
            'service_area': f"我们的服务范围覆盖{city['name']}及周边地区，包括{nearby_str}等城市。无论您住在哪个区域，我们都能为您提供及时的服务。",
            
            'service_features': f"我们的{service['name']}服务具有以下特点：专业团队、快速响应、质量保证、价格合理。我们致力于为{city['name']}地区的客户提供最优质的家电{service['name']}服务。",
            
            'why_choose_us': f"选择我们的{service['name']}服务，您将享受到专业的服务团队、完善的售后保障、合理的价格以及便捷的预约方式。我们深知{city['name']}地区客户的需求，能够为您提供最适合的解决方案。"
        }
        
        return sections
    
    def generate_keywords_list(self, city_key, service_key):
        """
        生成关键词列表
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            list: 关键词列表
        """
        from .config.seo_keywords import generate_keywords
        return generate_keywords(city_key, service_key)
    
    def get_breadcrumb_data(self, city_key, service_key):
        """
        生成面包屑导航数据
        
        Args:
            city_key: 城市键名
            service_key: 服务类型键名
        
        Returns:
            list: 面包屑导航数据
        """
        from .config.seo_keywords import get_city_by_slug, get_service_by_key
        city = get_city_by_slug(city_key)
        service = get_service_by_key(service_key)
        
        if not city or not service:
            return [{'name': '首页', 'url': '/'}]
        
        return [
            {'name': '首页', 'url': '/'},
            {'name': '服务', 'url': '/services/'},
            {'name': f"{city['name']} {service['name']}", 'url': f"/{city_key}/{service_key}/"}
        ]


def get_seo_data(city_key, service_key):
    """
    获取完整的SEO数据
    
    Args:
        city_key: 城市键名
        service_key: 服务类型键名
    
    Returns:
        dict: 完整的SEO数据字典
    """
    from .config.seo_keywords import get_city_by_slug, get_service_by_key, get_nearby_cities
    generator = SEOContentGenerator()
    
    # 获取城市和服务信息
    city_info = get_city_by_slug(city_key)
    service_info = get_service_by_key(service_key)
    
    # 为城市信息添加key字段
    if city_info:
        city_info['key'] = city_key
        # 获取附近城市信息，并添加key字段
        nearby_cities = get_nearby_cities(city_key)
        city_info['nearby_cities'] = []
        for nearby_city_name in nearby_cities:
            # 查找对应的城市键名
            for key, city_data in generator.cities.items():
                if city_data['name'] == nearby_city_name:
                    city_info['nearby_cities'].append({
                        'name': nearby_city_name,
                        'key': key
                    })
                    break
    
    # 为服务信息添加key字段
    if service_info:
        service_info['key'] = service_key
    
    return {
        'title': generator.generate_page_title(city_key, service_key),
        'meta_description': generator.generate_meta_description(city_key, service_key),
        'h1_title': generator.generate_h1_title(city_key, service_key),
        'content_sections': generator.generate_content_sections(city_key, service_key),
        'keywords': generator.generate_keywords_list(city_key, service_key),
        'breadcrumb': generator.get_breadcrumb_data(city_key, service_key),
        'city_info': city_info,
        'service_info': service_info,
        'services': generator.services  # 添加所有服务信息供模板使用
    }