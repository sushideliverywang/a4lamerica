from django import template
from django.utils import timezone
import pytz
from ..utils import encode_item_id

register = template.Library()

@register.filter
def filter_today(business_hours):
    """
    从营业时间列表中获取今天的营业时间
    考虑店铺所在位置的时区
    """
    if not business_hours:
        return None
    
    # 获取第一个营业时间记录的店铺时区
    location = business_hours.first().location
    location_tz = pytz.timezone(location.timezone)
    
    # 获取店铺所在位置的当前时间
    now = timezone.now()
    location_time = now.astimezone(location_tz)
    
    # 获取店铺所在位置的当前星期几
    today = location_time.weekday()
    # 将weekday()的结果转换为我们的DAYS_OF_WEEK格式
    # weekday()返回0-6（0是周一），我们需要转换为0-6（0是周日）
    today = (today + 1) % 7
    
    for hours in business_hours:
        if hours.day_of_week == today:
            return hours
    return None

@register.filter
def location_weekday(business_hours):
    """
    获取店铺所在位置的本地时间星期几
    """
    if not business_hours:
        return ""
    
    # 获取第一个营业时间记录的店铺时区
    location = business_hours.first().location
    location_tz = pytz.timezone(location.timezone)
    
    # 获取店铺所在位置的当前时间
    now = timezone.now()
    location_time = now.astimezone(location_tz)
    
    # 返回星期几的缩写（Mon, Tue, Wed, etc.）
    return location_time.strftime("%a")

@register.filter
def percent(value, decimals=2):
    """
    将浮点数转换为百分比格式
    """
    try:
        value = float(value)
        return f"{value * 100:.{int(decimals)}f}%"
    except (ValueError, TypeError):
        return value

@register.filter
def item_hash(item):
    """
    生成商品的哈希编码
    """
    try:
        return encode_item_id(item)
    except Exception:
        return str(item.id) if hasattr(item, 'id') else 'None'