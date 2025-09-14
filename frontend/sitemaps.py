"""
网站地图配置
为Appliances 4 Less Doraville创建完整的XML网站地图系统
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from .models_proxy import Location, Category, InventoryItem
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class StaticViewSitemap(Sitemap):
    """
    静态页面网站地图
    包括首页、政策页面等
    """
    priority = 1.0
    changefreq = 'weekly'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        return [
            'frontend:home',
            'frontend:privacy_policy',
            'frontend:terms_of_service',
            'frontend:cookie_policy',
        ]
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):
        # 静态页面使用当前时间作为最后修改时间
        return timezone.now()


class StoreSitemap(Sitemap):
    """
    商店页面网站地图
    包括所有商店位置页面
    """
    priority = 0.9
    changefreq = 'daily'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        try:
            # 只获取特定公司的商店
            company_id = getattr(settings, 'COMPANY_ID')
            return Location.objects.filter(
                company_id=company_id,
                is_active=True
            ).order_by('name')
        except Exception as e:
            logger.error(f"Error fetching stores for sitemap: {e}")
            return []
    
    def location(self, obj):
        return f'/{obj.slug}/'
    
    def lastmod(self, obj):
        # 使用商店的最后更新时间
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()


class CategorySitemap(Sitemap):
    """
    分类页面网站地图
    包括所有产品分类页面
    """
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        try:
            # 分类没有company字段，直接获取所有活跃分类
            return Category.objects.filter(
                slug__isnull=False
            ).exclude(slug='').order_by('name')
        except Exception as e:
            logger.error(f"Error fetching categories for sitemap: {e}")
            return []
    
    def location(self, obj):
        return f'/category/{obj.slug}/'
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()


class ProductSitemap(Sitemap):
    """
    产品页面网站地图
    包括所有产品详情页面
    """
    priority = 0.7
    changefreq = 'daily'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        try:
            # 只获取特定公司的产品
            company_id = getattr(settings, 'COMPANY_ID')
            return InventoryItem.objects.filter(
                company_id=company_id,
                published=True
            ).select_related('model_number', 'location').order_by('-created_at')
        except Exception as e:
            logger.error(f"Error fetching products for sitemap: {e}")
            return []
    
    def location(self, obj):
        # 使用产品哈希作为URL
        from .utils import get_item_hash
        item_hash = get_item_hash(obj)
        return f'/item/{item_hash}/'
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()
    
    def priority(self, obj):
        # 根据产品状态调整优先级
        if hasattr(obj, 'item_state') and obj.item_state:
            if obj.item_state.name.lower() in ['new', 'excellent']:
                return 0.9
            elif obj.item_state.name.lower() in ['good', 'fair']:
                return 0.7
            else:
                return 0.5
        return 0.7


class WarrantyPolicySitemap(Sitemap):
    """
    保修政策页面网站地图
    每个商店都有保修政策页面
    """
    priority = 0.6
    changefreq = 'monthly'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        try:
            company_id = getattr(settings, 'COMPANY_ID')
            return Location.objects.filter(
                company_id=company_id,
                is_active=True
            ).order_by('name')
        except Exception as e:
            logger.error(f"Error fetching stores for warranty sitemap: {e}")
            return []
    
    def location(self, obj):
        return f'/{obj.slug}/warranty/'
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()


class TermsConditionsSitemap(Sitemap):
    """
    条款和条件页面网站地图
    每个商店都有条款和条件页面
    """
    priority = 0.6
    changefreq = 'monthly'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        try:
            company_id = getattr(settings, 'COMPANY_ID')
            return Location.objects.filter(
                company_id=company_id,
                is_active=True
            ).order_by('name')
        except Exception as e:
            logger.error(f"Error fetching stores for terms sitemap: {e}")
            return []
    
    def location(self, obj):
        return f'/{obj.slug}/terms/'
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()
