"""
网站地图配置
为Appliances 4 Less Doraville创建完整的XML网站地图系统
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from .models_proxy import Location, Category, InventoryItem
from .config.seo_keywords import CITIES
from .config.product_seo_pages import get_active_seo_pages, build_product_filters
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

    def priority(self, item):
        """根据页面类型设置不同的优先级"""
        if item == 'frontend:home':
            return 1.0  # 首页最高优先级
        else:
            return 0.3  # 网站级政策页面很低优先级（法律合规但SEO价值低）

    def changefreq(self, item):
        """根据页面类型设置不同的更新频率"""
        if item == 'frontend:home':
            return 'daily'  # 首页每日更新
        else:
            return 'yearly'  # 网站级政策页面年更新（很少变化）


class IncomingInventorySitemap(Sitemap):
    """
    即将到货页面网站地图
    基于LoadManifest数据的动态页面
    """
    priority = 0.8  # 高优先级功能页面
    changefreq = 'weekly'  # 每周更新频率，符合货物到达频率
    protocol = 'https' if not settings.DEBUG else 'http'

    def items(self):
        # 返回单一页面标识符
        return ['incoming_inventory']

    def location(self, item):
        return reverse('frontend:incoming_inventory')

    def lastmod(self, item):
        """
        基于最新LoadManifest的更新时间
        这样能准确反映页面内容的实际变化
        """
        try:
            from .models_proxy import LoadManifest
            company_id = getattr(settings, 'COMPANY_ID')
            latest_manifest = LoadManifest.objects.filter(
                status=LoadManifest.Status.CONVERTING,
                company_id=company_id
            ).order_by('-updated_at').first()

            if latest_manifest and hasattr(latest_manifest, 'updated_at'):
                return latest_manifest.updated_at
            else:
                return timezone.now()
        except Exception as e:
            logger.error(f"Error getting incoming inventory lastmod: {e}")
            return timezone.now()

    def changefreq(self, item):
        """
        根据实际LoadManifest数据动态调整更新频率
        """
        try:
            from .models_proxy import LoadManifest
            from datetime import timedelta

            company_id = getattr(settings, 'COMPANY_ID')
            recent_manifests = LoadManifest.objects.filter(
                status=LoadManifest.Status.CONVERTING,
                company_id=company_id,
                updated_at__gte=timezone.now() - timedelta(days=30)
            ).count()

            # 根据最近30天的更新频率动态调整
            if recent_manifests >= 8:  # 每周都有更新
                return 'daily'
            elif recent_manifests >= 4:  # 每两周有更新
                return 'weekly'
            else:  # 更新较少
                return 'monthly'

        except Exception as e:
            logger.error(f"Error calculating incoming inventory changefreq: {e}")
            return 'weekly'  # 默认值


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
    priority = 0.9
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
    每个商店都有保修政策页面 - 本地SEO重要
    """
    priority = 0.7  # 提高优先级，有本地SEO价值
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
    每个商店都有条款和条件页面 - 本地SEO重要
    """
    priority = 0.7  # 提高优先级，有本地SEO价值
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


class SEOServiceListSitemap(Sitemap):
    """
    SEO服务列表页面网站地图
    包括通用服务页面和所有城市特定的服务页面
    """
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https' if not settings.DEBUG else 'http'
    
    def items(self):
        # 返回所有城市键名，包括通用服务页面
        items = []
        
        # 添加通用服务页面（无城市参数）
        items.append({
            'type': 'general',
            'city_key': None,
            'city_name': 'Services',
            'lastmod': timezone.now()
        })
        
        # 添加所有城市特定的服务页面
        for city_key, city_info in CITIES.items():
            items.append({
                'type': 'city',
                'city_key': city_key,
                'city_name': city_info['name'],
                'lastmod': timezone.now()
            })
        
        return items
    
    def location(self, obj):
        if obj['type'] == 'general':
            # 通用服务页面
            return reverse('frontend:seo_service_list')
        else:
            # 城市特定服务页面
            return reverse('frontend:seo_service_list', kwargs={'city_key': obj['city_key']})
    
    def lastmod(self, obj):
        return obj['lastmod']
    
    def priority(self, obj):
        # 通用服务页面优先级更高
        if obj['type'] == 'general':
            return 0.9
        else:
            return 0.8


class ProductSEOPageSitemap(Sitemap):
    """
    动态产品SEO页面网站地图
    包括所有配置且有足够库存的SEO页面
    """
    priority = 0.9  # 高优先级，因为这些是重要的SEO页面
    changefreq = 'daily'  # 日更新，因为库存可能变化
    protocol = 'https' if not settings.DEBUG else 'http'

    def items(self):
        """获取所有有效的SEO页面"""
        seo_pages = []
        active_pages = get_active_seo_pages()

        for page_key, page_config in active_pages.items():
            try:
                # 检查库存数量是否满足要求
                filters = build_product_filters(page_config)
                item_count = InventoryItem.objects.filter(filters).count()
                min_inventory = page_config.get('min_inventory', 1)

                # 只有满足最小库存要求的页面才加入sitemap
                if item_count >= min_inventory:
                    seo_pages.append({
                        'page_key': page_key,
                        'config': page_config,
                        'item_count': item_count,
                        'lastmod': timezone.now()  # 使用当前时间，实际项目中可考虑基于库存更新时间
                    })

            except Exception as e:
                # 如果查询失败，记录错误但不影响其他页面
                logger.error(f"Failed to check inventory for SEO page {page_key}: {e}")
                continue

        # 按优先级排序（首页显示的页面优先级更高）
        seo_pages.sort(key=lambda x: x['config'].get('homepage_priority', 999))

        return seo_pages

    def location(self, obj):
        """生成SEO页面的URL"""
        return reverse('frontend:product_seo_page', kwargs={'seo_page_key': obj['page_key']})

    def lastmod(self, obj):
        """返回页面最后修改时间"""
        return obj['lastmod']

    def priority(self, obj):
        """根据页面配置动态调整优先级"""
        config = obj['config']

        # 首页显示的页面优先级更高
        if config.get('show_on_homepage', False):
            return 0.95

        # 根据库存数量调整优先级
        item_count = obj['item_count']
        if item_count >= 10:
            return 0.9
        elif item_count >= 5:
            return 0.85
        else:
            return 0.8

    def changefreq(self, obj):
        """根据库存情况动态调整更新频率"""
        item_count = obj['item_count']

        # 库存较多的页面更新频率高
        if item_count >= 10:
            return 'daily'
        elif item_count >= 5:
            return 'weekly'
        else:
            return 'monthly'
