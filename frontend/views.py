from django.shortcuts import render, get_object_or_404, redirect
from .models_proxy import (
    Location, Address, LocationWarrantyPolicy, LocationTermsAndConditions,
    InventoryItem, ItemImage, ItemState, Category, ProductModel, ProductImage,
    CustomerFavorite, ShoppingCart, CustomerWarrantyPolicy, CustomerTermsAgreement,
    Order, OrderStatusHistory, TransactionRecord, CustomerAddress, StateTransition,
    InventoryStateHistory, LoadManifest,
    Company
)
from django.db import models
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, View
from django.http import Http404, JsonResponse, HttpResponse
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from scripts.address_validator import AddressValidator
from django.conf import settings
from googlemaps import Client
from django.views.decorators.http import require_POST, require_http_methods
from geopy.distance import geodesic
from decimal import Decimal
from django.db import transaction
import json
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, FormView
from decimal import Decimal
from django.utils.decorators import method_decorator
import pytz
import re
from .utils import decode_item_id, get_item_hash, get_seo_data
from .config.seo_keywords import CITIES, SERVICE_TYPES
from .config.product_seo_pages import (
    PRODUCT_SEO_PAGES, get_seo_page_config, build_product_filters, get_homepage_seo_pages
)
from .services.google_reviews import GoogleReviewsService
from django.views.decorators.csrf import csrf_exempt
import logging

# 在文件开头添加 Google Maps 客户端初始化
# 只有在有 API 密钥时才初始化客户端
if hasattr(settings, 'GOOGLE_MAPS_API_KEY') and settings.GOOGLE_MAPS_API_KEY:
    gmaps = Client(key=settings.GOOGLE_MAPS_API_KEY)  # 使用服务器端 API 密钥
else:
    gmaps = None


class BaseCompanyMixin:
    """
    公司过滤Mixin - 确保所有查询都限制在特定公司范围内
    这个项目只显示特定公司的数据，而不是所有公司的数据
    """
    
    def get_company_id(self):
        """获取配置的公司ID"""
        return getattr(settings, 'COMPANY_ID')
    
    def get_company_filtered_locations(self):
        """获取过滤后的店铺位置"""
        return Location.objects.filter(
            company_id=self.get_company_id(),
            is_active=True
        )
    
    def get_company_filtered_inventory_items(self):
        """获取过滤后的库存商品"""
        return InventoryItem.objects.filter(
            location__company_id=self.get_company_id(),
            published=True
        )
    
    def get_company_filtered_orders(self):
        """获取过滤后的订单"""
        return Order.objects.filter(
            company_id=self.get_company_id()
        )

class BaseFrontendMixin(BaseCompanyMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent_category_id__isnull=True)
        # 为所有页面提供stores数据，用于优化图片预加载
        context['stores'] = self.get_company_filtered_locations().filter(location_type='STORE')
        return context


class DetailViewMixin(BaseCompanyMixin):
    """专门用于DetailView的Mixin，提供分类数据"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent_category_id__isnull=True)
        # 为所有页面提供stores数据，用于优化图片预加载
        context['stores'] = self.get_company_filtered_locations().filter(location_type='STORE')
        return context


class PrivacyPolicyView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/privacy_policy.html'

class TermsOfServiceView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/terms_of_service.html'

class CookiePolicyView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/cookie_policy.html'

class AboutUsView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/about_us.html'

class ContactUsView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/contact_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取所有店铺的location信息
        context['stores'] = self.get_company_filtered_locations().filter(location_type='STORE')
        return context

class ReturnPolicyView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/return_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取所有店铺的location信息，用于展示warranty policy链接
        context['stores'] = self.get_company_filtered_locations().filter(location_type='STORE')
        return context


class HomeView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取配置公司的所有活跃店铺，预加载营业时间数据
        stores = self.get_company_filtered_locations().filter(
            location_type='STORE'
        ).select_related('company', 'address').prefetch_related('business_hours').only(
            'name', 'address__street_number', 'address__street_name', 'address__city', 
            'address__state', 'address__zip_code', 'address__latitude', 'address__longitude',
            'image', 'company__company_name', 'timezone'
        )
        
        
        # 为首页创建简化的城市数据，只包含必要的字段
        minimal_cities = {}
        for city_key, city_info in CITIES.items():
            minimal_cities[city_key] = {
                'name': city_info['name'],
                'image_desktop': city_info['image_desktop'],
                'image_mobile': city_info.get('image_mobile', city_info['image_desktop'])
            }

        # 获取首页显示的SEO页面
        homepage_seo_pages = get_homepage_seo_pages()

        # 为每个SEO页面添加库存数量
        seo_pages_with_counts = []
        for seo_page in homepage_seo_pages:
            page_config = seo_page['config']
            try:
                # 构建筛选条件并查询库存数量
                filters = build_product_filters(page_config)
                item_count = self.get_company_filtered_inventory_items().filter(filters).count()

                # 只有满足最小库存要求的页面才显示
                min_inventory = page_config.get('min_inventory', 1)
                if item_count >= min_inventory:
                    seo_pages_with_counts.append({
                        'key': seo_page['key'],
                        'config': page_config,
                        'item_count': item_count
                    })
            except Exception as e:
                # 如果查询失败，记录错误但不影响页面加载
                logging.error(f"Failed to get item count for SEO page {seo_page['key']}: {e}")
                continue

        # 获取Google评论 (多语言评论，只显示5星好评)
        google_service = GoogleReviewsService()
        google_reviews = google_service.get_reviews(max_reviews=6, min_rating=5, show_multilingual=True)

        # 检查是否有即将到货的库存
        has_incoming_inventory = self._check_incoming_inventory()

        # 特色分类配置 - 用于新的首页分类展示
        FEATURED_CATEGORIES = [
            {'slug': 'refrigerator', 'name': 'Refrigerator', 'image': 'refrigerator.webp'},
            {'slug': 'range', 'name': 'Range', 'image': 'range.webp'},
            {'slug': 'dishwasher', 'name': 'Dishwasher', 'image': 'dishwasher.webp'},
            {'slug': 'microwave', 'name': 'Microwave', 'image': 'microwave.webp'},
            {'slug': 'wall-oven', 'name': 'Wall Oven', 'image': 'wall_oven.webp'},
            {'slug': 'wine-cooler', 'name': 'Wine Cooler', 'image': 'wine_cooler.webp'},
            {'slug': 'washer', 'name': 'Washer', 'image': 'washer.webp'},
            {'slug': 'dryer', 'name': 'Dryer', 'image': 'dryer.webp'},
            {'slug': 'wash-tower', 'name': 'Wash Tower', 'image': 'wash_tower.webp'},
            {'slug': 'washerdryer-combo', 'name': 'Washer/Dryer Combo', 'image': 'washerdryer_combo.webp'},
        ]

        # 为特色分类计算商品数量
        featured_categories = []
        for cat_config in FEATURED_CATEGORIES:
            try:
                category = Category.objects.get(slug=cat_config['slug'])

                # 使用与现有category_items相同的逻辑计算商品数量
                base_items = self.get_company_filtered_inventory_items().filter(
                    models.Q(model_number__category=category) |
                    models.Q(model_number__category__parent_category_id=category.id),
                    published=True,
                    current_state_id__in=[4, 5, 8]
                )

                total_count = base_items.count()

                featured_categories.append({
                    'slug': cat_config['slug'],
                    'name': cat_config['name'],
                    'image': cat_config['image'],
                    'count': total_count,
                    'category_obj': category
                })

            except Category.DoesNotExist:
                # 如果分类不存在，记录但继续处理其他分类
                logging.warning(f"Featured category not found: {cat_config['slug']}")
                continue

        context.update({
            'stores': stores,
            'cities': minimal_cities,
            'homepage_seo_pages': seo_pages_with_counts,
            'google_reviews': google_reviews,
            'has_incoming_inventory': has_incoming_inventory,
            'featured_categories': featured_categories,
        })
        return context

    def _check_incoming_inventory(self):
        """
        检查是否有即将到货的库存
        使用与IncomingInventoryView相同的逻辑
        """
        # 使用与IncomingInventoryView相同的过滤逻辑
        tracking_states = [1, 2, 3]  # 追踪的状态ID

        # 获取状态为CONVERTING的LoadManifest，使用配置中的公司ID
        load_manifests = LoadManifest.objects.filter(
            status=LoadManifest.Status.CONVERTING,
            company_id=settings.COMPANY_ID
        )

        # 检查是否有任何批次包含即将到货的商品
        for manifest in load_manifests:
            inventory_items = InventoryItem.objects.filter(
                load_number=manifest,
                current_state_id__in=tracking_states
            )
            if inventory_items.exists():
                return True
        
        return False


class StoreView(BaseFrontendMixin, TemplateView):
    """商店页面 - 显示特定商店的所有产品"""
    template_name = 'frontend/store.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_slug = kwargs['location_slug']
        
        # 排除已知的系统路径，避免与StoreView冲突
        excluded_slugs = {
            'admin', 'organization', 'inventory', 'product', 'accounts', 
            'dashboard', 'order', 'financial', 'delivery', 'api', 'static',
            'media', 'cart', 'search', 'customer', 'item', 'category',
            'privacy-policy', 'terms-of-service', 'cookie-policy'
        }
        
        if location_slug in excluded_slugs:
            raise Http404("Page not found")
        
        location = get_object_or_404(
            self.get_company_filtered_locations().select_related('address', 'company').prefetch_related('business_hours'),
            slug=location_slug
        )

        # 获取当前商店的所有商品（按分类分组）
        category_items = {}
        for category in context['categories']:
            
            # 获取当前类别及其所有子类别的商品，但只显示当前商店的商品
            # 只显示状态为 WAITING FOR TESTING (4), TEST (5), FOR SALE (8) 的商品
            base_items = self.get_company_filtered_inventory_items().filter(
                models.Q(model_number__category=category) |  # 当前类别的商品
                models.Q(model_number__category__parent_category_id=category.id),  # 子类别的商品
                published=True,
                location=location,  # 只显示当前商店的商品
                current_state_id__in=[4, 5, 8]  # 只显示这三种状态的商品
            ).select_related(
                'model_number',
                'model_number__brand',
                'model_number__category',
                'location'
            ).annotate(
                favorite_count=Count('favorited_by', distinct=True)
            ).only(
                'id',
                'retail_price',
                'model_number__model_number',
                'model_number__msrp',
                'model_number__brand__name',
                'model_number__category__name',
                'location__name'
            )
            
            
            # 分别处理有商品图片和没有商品图片的商品
            items_with_images = base_items.filter(images__isnull=False).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=ItemImage.objects.only('image').order_by('display_order')[:1],
                    to_attr='item_images'
                )
            )
            
            items_without_images = base_items.filter(images__isnull=True).prefetch_related(
                models.Prefetch(
                    'model_number__images',
                    queryset=ProductImage.objects.only('image').order_by('id')[:1],
                    to_attr='model_images'
                )
            )
            
            # 合并两个查询集
            items = list(items_with_images) + list(items_without_images)
            
            if items:
                # 计算真实的产品总数
                total_count = len(items)
                
                # 限制每个分类只显示6个产品
                items = items[:6]
                
                # 为每个商品计算节省金额
                for item in items:
                    if item.model_number.msrp:
                        item.savings = item.model_number.msrp - item.retail_price
                        item.savings_percentage = (item.savings / item.model_number.msrp) * 100
                    else:
                        item.savings = 0
                        item.savings_percentage = 0
                
                # 将真实总数添加到每个商品对象中，供模板使用
                for item in items:
                    item.total_category_count = total_count
                
                category_items[category] = items
        
        context.update({
            'location': location,
            'category_items': category_items,
            'is_logged_in': self.request.user.is_authenticated,
        })
        return context


class ItemDetailView(DetailViewMixin, DetailView):
    model = InventoryItem
    template_name = 'frontend/item_detail.html'
    context_object_name = 'item'
    
    def get_queryset(self):
        """获取所有商品，移除published和状态限制避免404错误，只显示配置公司的商品"""
        return self.get_company_filtered_inventory_items().select_related(
            # 移除所有限制: published=True, current_state_id__in=[4, 5, 8]
            'model_number',
            'model_number__brand',
            'model_number__category',
            'location',
            'location__address'
        ).prefetch_related(
            'model_number__specs',
            'model_number__specs__spec'
        )
    
    def get_object(self, queryset=None):
        """根据哈希编码获取商品对象"""
        # 从URL参数中获取哈希编码
        item_hash = self.kwargs.get('item_hash')
        
        if not item_hash:
            raise Http404("Invalid item URL")
        
        # 解码哈希获取商品
        item = decode_item_id(item_hash)
        
        if not item:
            raise Http404("Item not found")
        
        return item
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['item']
        
        # 按需加载图片：如果商品有图片则加载商品图片，否则加载产品型号图片
        if item.images.exists():
            # 商品有图片，加载所有商品图片
            item_images = ItemImage.objects.filter(
                item=item
            ).only('image').order_by('display_order')
            item.item_images = list(item_images)
        else:
            # 商品没有图片，加载所有产品型号图片
            model_images = ProductImage.objects.filter(
                product_model=item.model_number
            ).only('image').order_by('id')
            item.item_images = list(model_images)
        
        # 计算节省金额
        if item.model_number.msrp:
            item.savings = item.model_number.msrp - item.retail_price
            item.savings_percentage = (item.savings / item.model_number.msrp) * 100
        else:
            item.savings = 0
            item.savings_percentage = 0
        
        # 格式化保修期限显示
        if item.warranty_period:
            warranty_days = int(item.warranty_period)
            if warranty_days == 0:
                item.warranty_display = "No Warranty"
            elif warranty_days == 365:
                item.warranty_display = "1 Year"
            elif warranty_days == 730:
                item.warranty_display = "2 Years"
            elif warranty_days == 1095:
                item.warranty_display = "3 Years"
            elif warranty_days == 1460:
                item.warranty_display = "4 Years"
            elif warranty_days == 1825:
                item.warranty_display = "5 Years"
            elif warranty_days < 30:
                item.warranty_display = f"{warranty_days} Days"
            else:
                months = warranty_days // 30
                item.warranty_display = f"{months} Months"
        else:
            item.warranty_display = "No Warranty"
        
        # 检查商品状态
        is_available = (
            item.published and
            item.current_state_id in [4, 5, 8] and
            item.order is None
        )

        # 区分已售出和其他不可用状态
        is_sold = item.order is not None  # 有订单就是已售出
        is_not_available = (
            not item.published and item.order is None  # 主动下架或其他原因
        ) or (
            item.published and item.current_state_id not in [4, 5, 8]  # 状态不可售
        )

        # 获取相似商品（所有商品都显示，不管是否已售）
        similar_items = self.get_company_filtered_inventory_items().filter(
            model_number__category=item.model_number.category,
            published=True,
            current_state_id__in=[4, 5, 8]  # 只推荐可售的商品
        ).exclude(id=item.id).select_related(
            'model_number',
            'model_number__brand'
        )[:4]

        # 为相似商品计算节省金额和加载图片
        for similar_item in similar_items:
            if similar_item.model_number.msrp:
                similar_item.savings = similar_item.model_number.msrp - similar_item.retail_price
                similar_item.savings_percentage = (similar_item.savings / similar_item.model_number.msrp) * 100
            else:
                similar_item.savings = 0
                similar_item.savings_percentage = 0

        # 获取收藏总数 - 对所有用户显示
        context.update({
            'is_available': is_available,
            'is_sold': is_sold,
            'is_not_available': is_not_available,
            'similar_items': similar_items,
            'favorite_count': CustomerFavorite.objects.filter(item=item).count(),
            'breadcrumbs': [
                {'name': 'Home', 'url': reverse('frontend:home')},
                {'name': item.model_number.category.name, 'url': reverse('frontend:category', args=[item.model_number.category.slug])},
                {'name': item.model_number.model_number, 'url': '#'}
            ]
        })
        
        # 如果用户已登录，获取个人收藏和购物车状态
        if self.request.user.is_authenticated:
            try:
                customer = self.request.user.customer
                
                # 检查是否已收藏
                context['is_favorited'] = CustomerFavorite.objects.filter(
                    customer=customer,
                    item=item
                ).exists()
                
                # 检查是否在购物车中
                context['is_in_cart'] = ShoppingCart.objects.filter(
                    customer=customer,
                    item=item
                ).exists()
                
            except Exception:
                # 如果获取用户信息失败，保持默认值
                context.update({
                    'is_favorited': False,
                    'is_in_cart': False
                })
        else:
            # 未登录用户设置默认值
            context.update({
                'is_favorited': False,
                'is_in_cart': False
            })
        
        return context

class CategoryView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        store_slug = self.request.GET.get('store')
        
        # 获取当前类别
        category = Category.objects.get(slug=category_slug)
        
        # 检查是否有store参数
        store = None
        if store_slug:
            try:
                store = self.get_company_filtered_locations().get(slug=store_slug)
            except Location.DoesNotExist:
                store = None
        
        # 检查是否有子类别
        has_subcategories = Category.objects.filter(parent_category_id=category.id).exists()
        
        # 获取当前类别的商品（不属于任何子类别的商品），只显示配置公司的商品
        base_items = self.get_company_filtered_inventory_items().filter(
            model_number__category=category,
            published=True
        ).select_related(
            'model_number',
            'model_number__brand'
        ).annotate(
            favorite_count=Count('favorited_by', distinct=True)
        ).only(
            'id',
            'retail_price',
            'model_number__model_number',
            'model_number__msrp',
            'model_number__brand__name'
        )
        
        # 如果有store参数，只显示该store的商品
        if store:
            base_items = base_items.filter(location=store)
        
        # 分别处理有商品图片和没有商品图片的商品
        items_with_images = base_items.filter(images__isnull=False).prefetch_related(
            models.Prefetch(
                'images',
                queryset=ItemImage.objects.only('image').order_by('display_order')[:1],  # 只加载第一张图片
                to_attr='item_images'
            )
        )
        
        # 对于没有商品图片的商品，预加载产品型号图片
        items_without_images = base_items.filter(images__isnull=True).prefetch_related(
            models.Prefetch(
                'model_number__images',
                queryset=ProductImage.objects.only('image').order_by('id')[:1],  # 预加载产品型号的第一张图片
                to_attr='model_images'
            )
        )
        
        # 合并两个查询集
        current_category_items = list(items_with_images) + list(items_without_images)
        
        # 为当前类别的商品计算节省金额
        for item in current_category_items:
            if item.model_number.msrp:
                item.savings = item.model_number.msrp - item.retail_price
                item.savings_percentage = (item.savings / item.model_number.msrp) * 100
            else:
                item.savings = 0
                item.savings_percentage = 0
        
        if has_subcategories:
            # 如果有子类别，获取所有子类别
            subcategories = Category.objects.filter(parent_category_id=category.id)
            category_items = {}
            
            # 获取每个子类别的商品，只显示配置公司的商品
            for subcategory in subcategories:
                base_items = self.get_company_filtered_inventory_items().filter(
                    model_number__category=subcategory,
                    published=True
                ).select_related(
                    'model_number',
                    'model_number__brand'
                ).annotate(
                    favorite_count=Count('favorited_by', distinct=True)
                ).only(
                    'id',
                    'retail_price',
                    'model_number__model_number',
                    'model_number__msrp',
                    'model_number__brand__name'
                )
                
                # 如果有store参数，只显示该store的商品
                if store:
                    base_items = base_items.filter(location=store)
                
                # 分别处理有商品图片和没有商品图片的商品
                items_with_images = base_items.filter(images__isnull=False).prefetch_related(
                    models.Prefetch(
                        'images',
                        queryset=ItemImage.objects.only('image').order_by('display_order')[:1],  # 只加载第一张图片
                        to_attr='item_images'
                    )
                )
                
                # 对于没有商品图片的商品，预加载产品型号图片
                items_without_images = base_items.filter(images__isnull=True).prefetch_related(
                    models.Prefetch(
                        'model_number__images',
                        queryset=ProductImage.objects.only('image').order_by('id')[:1],  # 预加载产品型号的第一张图片
                        to_attr='model_images'
                    )
                )
                
                # 合并两个查询集
                items = list(items_with_images) + list(items_without_images)
                
                # 计算每个商品的节省金额
                for item in items:
                    if item.model_number.msrp:
                        item.savings = item.model_number.msrp - item.retail_price
                        item.savings_percentage = (item.savings / item.model_number.msrp) * 100
                    else:
                        item.savings = 0
                        item.savings_percentage = 0
                
                if items:
                    category_items[subcategory] = items
        else:
            category_items = {}
        
        # 构建面包屑导航
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('frontend:home')}
        ]
        
        # 如果有store参数，添加store到面包屑
        if store:
            breadcrumbs.append({
                'name': store.name,
                'url': reverse('frontend:store', args=[store.slug])
            })
        
        # 如果有父类别，添加父类别
        if category.parent_category_id:
            parent_category = Category.objects.get(id=category.parent_category_id)
            parent_url = reverse('frontend:category', args=[parent_category.slug])
            if store:
                parent_url += f'?store={store.slug}'
            breadcrumbs.append({
                'name': parent_category.name,
                'url': parent_url
            })
        
        # 添加当前类别
        current_url = reverse('frontend:category', args=[category.slug])
        if store:
            current_url += f'?store={store.slug}'
        breadcrumbs.append({
            'name': category.name,
            'url': current_url
        })
        
        context.update({
            'category': category,
            'has_subcategories': has_subcategories,
            'category_items': category_items,
            'current_category_items': current_category_items,
            'breadcrumbs': breadcrumbs,
            'store': store,
            'is_store_mode': store is not None
        })
        return context
    
class CustomerDashboardView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/customer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        
        # 获取客户的所有订单，按创建时间倒序排列，只显示配置公司的订单
        orders = customer.order_set.filter(
            company_id=self.get_company_id()
        ).select_related(
            'company', 'location', 'location__address'
        ).order_by('-created_at')
        
        # 为每个订单添加paid_amount和balance属性，以及时区信息
        for order in orders:
            order.paid_amount = order.calculate_paid_amount()
            order.balance = order.calculate_order_balance()
            # 添加时区信息
            order.location_timezone = order.location.timezone
        
        context.update({
            'orders': orders
        })
        return context

class CustomerProfileView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/customer_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context.update({
            'addresses': customer.addresses.all(),
            'GOOGLE_MAPS_CLIENT_API_KEY': settings.GOOGLE_MAPS_CLIENT_API_KEY
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        customer = request.user.customer
        address_validator = AddressValidator(settings.GOOGLE_MAPS_API_KEY)

        if action == 'update_profile':
            try:
                # 获取并验证数据
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                phone = request.POST.get('phone', '').strip()

                # 验证必填字段
                if not first_name:
                    return JsonResponse({'status': 'error', 'message': 'First name is required.'})
                if not last_name:
                    return JsonResponse({'status': 'error', 'message': 'Last name is required.'})

                # 更新用户信息
                user = request.user
                user.first_name = first_name
                user.last_name = last_name
                user.save(update_fields=['first_name', 'last_name'])

                # 更新客户信息
                customer.phone = phone
                customer.save(update_fields=['phone'])

                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile updated successfully.',
                    'profile': {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'phone': customer.phone
                    }
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to update profile: {str(e)}'
                })

        elif action == 'add_address':
            try:
                # 验证必填字段
                required_fields = ['street_address', 'city', 'state', 'zip_code']
                for field in required_fields:
                    value = request.POST.get(field, '').strip()
                    if not value:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'{field.replace("_", " ").title()} is required.'
                        })

                # 准备地址数据
                address_data = {
                    'street_address': request.POST.get('street_address', '').strip(),
                    'apartment_suite': request.POST.get('apartment_suite', '').strip(),
                    'city': request.POST.get('city', '').strip(),
                    'state': request.POST.get('state', '').strip(),
                    'zip_code': request.POST.get('zip_code', '').strip(),
                    'country': 'US'
                }

                # 验证地址
                is_valid, standardized_address, error_message = address_validator.validate_address_legacy(address_data)
                if not is_valid:
                    return JsonResponse({
                        'status': 'error',
                        'message': error_message
                    })

                # 创建新地址
                address = CustomerAddress.objects.create(
                    customer=customer,
                    street_address=standardized_address['street_address'],
                    apartment_suite=address_data['apartment_suite'],
                    city=standardized_address['city'],
                    state=standardized_address['state'],
                    zip_code=standardized_address['zip_code'],
                    country=standardized_address['country'],
                    is_default=request.POST.get('is_default') == 'true',
                    formatted_address=standardized_address['formatted_address'],
                    latitude=standardized_address['latitude'],
                    longitude=standardized_address['longitude'],
                    is_verified=True
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Address added successfully.',
                    'address': {
                        'id': address.id,
                        'street_address': address.street_address,
                        'apartment_suite': address.apartment_suite,
                        'city': address.city,
                        'state': address.state,
                        'zip_code': address.zip_code,
                        'country': address.country,
                        'is_default': address.is_default,
                        'formatted_address': address.formatted_address
                    }
                })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'edit_address':
            try:
                address_id = request.POST.get('address_id')
                if not address_id:
                    return JsonResponse({'status': 'error', 'message': 'Address ID is required.'})

                # 验证必填字段
                required_fields = ['street_address', 'city', 'state', 'zip_code']
                for field in required_fields:
                    value = request.POST.get(field, '').strip()
                    if not value:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'{field.replace("_", " ").title()} is required.'
                        })

                address = CustomerAddress.objects.get(
                    id=address_id,
                    customer=customer
                )

                # 准备地址数据
                address_data = {
                    'street_address': request.POST.get('street_address', '').strip(),
                    'apartment_suite': request.POST.get('apartment_suite', '').strip(),
                    'city': request.POST.get('city', '').strip(),
                    'state': request.POST.get('state', '').strip(),
                    'zip_code': request.POST.get('zip_code', '').strip(),
                    'country': 'US'
                }

                # 验证地址
                is_valid, standardized_address, error_message = address_validator.validate_address_legacy(address_data)
                if not is_valid:
                    return JsonResponse({
                        'status': 'error',
                        'message': error_message
                    })

                # 更新地址信息
                address.street_address = standardized_address['street_address']
                address.apartment_suite = address_data['apartment_suite']
                address.city = standardized_address['city']
                address.state = standardized_address['state']
                address.zip_code = standardized_address['zip_code']
                address.country = standardized_address['country']
                address.is_default = request.POST.get('is_default') == 'true'
                address.formatted_address = standardized_address['formatted_address']
                address.latitude = standardized_address['latitude']
                address.longitude = standardized_address['longitude']
                address.is_verified = True
                address.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Address updated successfully.',
                    'address': {
                        'id': address.id,
                        'street_address': address.street_address,
                        'apartment_suite': address.apartment_suite,
                        'city': address.city,
                        'state': address.state,
                        'zip_code': address.zip_code,
                        'country': address.country,
                        'is_default': address.is_default,
                        'formatted_address': address.formatted_address
                    }
                })
            except CustomerAddress.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Address not found.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'get_address_suggestions':
            try:
                partial_address = request.POST.get('address', '').strip()
                if not partial_address:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Address input is required.'
                    })

                # 使用 Google Places API 获取地址建议
                autocomplete_result = gmaps.places_autocomplete(
                    partial_address,
                    components={'country': 'us'},
                    types=['address']
                )
                
                suggestions = []
                for prediction in autocomplete_result:
                    # 获取每个建议的详细信息
                    place_details = gmaps.place(
                        prediction['place_id'],
                        fields=['address_component', 'formatted_address']
                    )
                    
                    if place_details['status'] == 'OK':
                        result = place_details['result']
                        address_components = result['address_components']
                        
                        # 解析地址组件
                        address = {
                            'street_address': '',
                            'city': '',
                            'state': '',
                            'zip_code': '',
                            'country': 'US'
                        }
                        
                        for component in address_components:
                            types = component['types']
                            if 'street_number' in types:
                                address['street_address'] = component['long_name']
                            elif 'route' in types:
                                address['street_address'] += ' ' + component['long_name']
                            elif 'locality' in types:
                                address['city'] = component['long_name']
                            elif 'administrative_area_level_1' in types:
                                address['state'] = component['short_name']
                            elif 'postal_code' in types:
                                address['zip_code'] = component['long_name']
                        
                        suggestions.append({
                            'place_id': prediction['place_id'],
                            'description': prediction['description'],
                            'address': address
                        })

                return JsonResponse({
                    'status': 'success',
                    'suggestions': suggestions
                })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'get_address_details':
            try:
                place_id = request.POST.get('place_id')
                if not place_id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Place ID is required.'
                    })

                # 使用 Google Places API 获取地址详情
                place_details = gmaps.place(place_id, fields=['address_component', 'formatted_address'])
                
                if place_details['status'] == 'OK':
                    result = place_details['result']
                    address_components = result['address_components']
                    
                    # 初始化地址组件
                    address = {
                        'street_address': '',
                        'city': '',
                        'state': '',
                        'zip_code': '',
                        'country': 'US'
                    }
                    
                    # 解析地址组件
                    for component in address_components:
                        types = component['types']
                        if 'street_number' in types:
                            address['street_address'] = component['long_name']
                        elif 'route' in types:
                            address['street_address'] += ' ' + component['long_name']
                        elif 'locality' in types:
                            address['city'] = component['long_name']
                        elif 'administrative_area_level_1' in types:
                            address['state'] = component['short_name']
                        elif 'postal_code' in types:
                            address['zip_code'] = component['long_name']
                    
                    return JsonResponse({
                        'status': 'success',
                        'address': address
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to get address details.'
                    })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'delete_address':
            try:
                address_id = request.POST.get('address_id')
                if not address_id:
                    return JsonResponse({'status': 'error', 'message': 'Address ID is required.'})

                address = CustomerAddress.objects.get(
                    id=address_id,
                    customer=customer
                )
                
                # 如果删除的是默认地址，且还有其他地址，则将第一个地址设为默认
                if address.is_default:
                    other_addresses = CustomerAddress.objects.filter(customer=customer).exclude(id=address_id)
                    if other_addresses.exists():
                        other_addresses.first().is_default = True
                        other_addresses.first().save()

                address.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Address deleted successfully.'
                })
            except CustomerAddress.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Address not found.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid action.'})

class CustomerFavoriteView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/customer_favorite.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 首先获取当前用户收藏的商品ID列表
        favorite_item_ids = CustomerFavorite.objects.filter(
            customer=self.request.user.customer
        ).values_list('item_id', flat=True)
        
        # 然后查询这些商品的信息，只显示配置公司的商品
        base_items = self.get_company_filtered_inventory_items().filter(
            id__in=favorite_item_ids
        ).select_related(
            'model_number',
            'model_number__brand',
            'model_number__category'
        ).annotate(
            # 获取每个商品被所有用户收藏的总数
            favorite_count=Count('favorited_by', distinct=True)
        ).only(
            'id',
            'retail_price',
            'model_number__model_number',
            'model_number__msrp',
            'model_number__brand__name',
            'model_number__category__name'
        )
        
        # 分别处理有商品图片和没有商品图片的商品
        items_with_images = base_items.filter(images__isnull=False).prefetch_related(
            models.Prefetch(
                'images',
                queryset=ItemImage.objects.only('image').order_by('display_order')[:1],  # 只加载第一张图片
                to_attr='item_images'
            )
        )
        
        # 对于没有商品图片的商品，预加载产品型号图片
        items_without_images = base_items.filter(images__isnull=True).prefetch_related(
            models.Prefetch(
                'model_number__images',
                queryset=ProductImage.objects.only('image').order_by('id')[:1],  # 预加载产品型号的第一张图片
                to_attr='model_images'
            )
        )
        
        # 合并两个查询集
        favorite_items = list(items_with_images) + list(items_without_images)
        
        # 按类别分组商品
        category_items = {}
        for item in favorite_items:
            category = item.model_number.category
            if category not in category_items:
                category_items[category] = []
            category_items[category].append(item)
            
            # 计算节省金额
            if item.model_number.msrp:
                item.savings = item.model_number.msrp - item.retail_price
                item.savings_percentage = (item.savings / item.model_number.msrp) * 100
            else:
                item.savings = 0
                item.savings_percentage = 0
        
        # 构建面包屑导航
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('frontend:home')},
            {'name': 'Favorite Items', 'url': reverse('frontend:customer_favorites')}
        ]
        
        context.update({
            'category_items': category_items,
            'breadcrumbs': breadcrumbs
        })
        return context

@login_required
def toggle_favorite(request, item_hash):
    """处理商品收藏/取消收藏"""
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': '请先登录',
            'code': 'not_authenticated'
        }, status=403, content_type='application/json')

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405, content_type='application/json')

    try:
        # 解码哈希获取商品
        item = decode_item_id(item_hash)
        if not item:
            return JsonResponse({
                'success': False,
                'error': 'Item not found'
            }, status=404, content_type='application/json')
        
        customer = request.user.customer
        
        # 检查当前收藏状态
        current_favorite = CustomerFavorite.objects.filter(
            customer=customer,
            item=item
        ).first()
        
        if current_favorite:
            # 如果已经收藏，则取消收藏
            current_favorite.delete()
            is_favorited = False
        else:
            # 创建新的收藏
            CustomerFavorite.objects.create(
                customer=customer,
                item=item
            )
            is_favorited = True
            
        # 获取最新的收藏数量
        favorite_count = CustomerFavorite.objects.filter(item=item).count()
        
        response_data = {
            'success': True,
            'is_favorited': is_favorited,
            'favorite_count': favorite_count
        }
        
        return JsonResponse(response_data, content_type='application/json')
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500, content_type='application/json')

class ShoppingCartView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/shopping_cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取当前用户的购物车商品
        base_cart_items = ShoppingCart.objects.filter(
            customer=self.request.user.customer
        ).select_related(
            'item',
            'item__model_number',
            'item__model_number__brand',
            'item__location',
            'item__location__address'
        )
        
        # 分别处理有商品图片和没有商品图片的商品
        cart_items_with_images = base_cart_items.filter(item__images__isnull=False).prefetch_related(
            'item__images'
        )
        
        # 对于没有商品图片的商品，预加载产品型号图片
        cart_items_without_images = base_cart_items.filter(item__images__isnull=True).prefetch_related(
            'item__model_number__images'
        )
        
        # 合并两个查询集
        cart_items = list(cart_items_with_images) + list(cart_items_without_images)
        
        # 获取每个商品的受欢迎程度（被多少个不同客户添加到购物车）
        item_popularity_counts = {}
        # 查询每个商品被多少个不同客户添加到购物车
        for cart_item in base_cart_items:
            item_id = cart_item.item.id
            if item_id not in item_popularity_counts:
                # 查询该商品被多少个不同客户添加到购物车
                popularity_count = ShoppingCart.objects.filter(
                    item_id=item_id
                ).values('customer').distinct().count()
                item_popularity_counts[item_id] = popularity_count
        
        # 获取用户地址
        addresses = CustomerAddress.objects.filter(customer=self.request.user.customer)
        default_address = addresses.filter(is_default=True).first()
        if not default_address and addresses.exists():
            default_address = addresses.first()
        
        # 按 location 分组并计算每个 location 的总价
        location_items = {}
        for cart_item in base_cart_items:
            location = cart_item.item.location
            if location:
                if location not in location_items:
                    location_items[location] = {
                        'items': [],
                        'total_price': 0,
                        'sales_tax': 0
                    }
                
                # 为购物车项目设置图片
                if cart_item.item.images.exists():
                    cart_item.item.item_images = [cart_item.item.images.first()]
                else:
                    cart_item.item.model_number.model_images = [cart_item.item.model_number.images.first()] if cart_item.item.model_number.images.exists() else []
                
                # 添加购物车计数到商品信息中
                cart_item.popularity_count = item_popularity_counts[cart_item.item.id]
                
                location_items[location]['items'].append(cart_item)
                location_items[location]['total_price'] += cart_item.price_at_add
                # 计算销售税
                location_items[location]['sales_tax'] = location_items[location]['total_price'] * location.sales_tax_rate
        
        # 构建面包屑导航
        breadcrumbs = [
            {'name': 'Home', 'url': reverse('frontend:home')},
            {'name': 'Shopping Cart', 'url': reverse('frontend:shopping_cart')}
        ]
        
        context.update({
            'location_items': location_items,
            'addresses': addresses,
            'default_address': default_address,
            'breadcrumbs': breadcrumbs,
            'GOOGLE_MAPS_CLIENT_API_KEY': settings.GOOGLE_MAPS_CLIENT_API_KEY
        })
        
        return context

@login_required
def calculate_distances(request):
    """计算购物车商品与新选择地址的距离"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        address_id = request.POST.get('address_id')
        if not address_id:
            return JsonResponse({'error': 'Address ID is required'}, status=400)
        
        # 获取选择的地址
        address = CustomerAddress.objects.get(id=address_id, customer=request.user.customer)
        
        # 获取购物车商品
        cart_items = ShoppingCart.objects.filter(
            customer=request.user.customer
        ).select_related(
            'item__location__address'
        )
        
        # 计算每个商品的距离
        distances = {}
        for item in cart_items:
            if item.item.location and item.item.location.address:
                distance = round(geodesic(
                    (item.item.location.address.latitude, item.item.location.address.longitude),
                    (address.latitude, address.longitude)
                ).miles, 1)
                distances[item.id] = distance
        
        return JsonResponse({
            'success': True,
            'distances': distances
        })
        
    except CustomerAddress.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def add_to_cart(request, item_hash):
    """添加商品到购物车"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)

    try:
        # 解码哈希获取商品
        item = decode_item_id(item_hash)
        if not item:
            return JsonResponse({
                'success': False,
                'error': 'Item not found'
            }, status=404)
        
        customer = request.user.customer

        # 检查商品是否可购买（状态检查和是否已售出）
        if item.current_state_id not in [4, 5, 8] or item.order is not None:
            return JsonResponse({
                'success': False,
                'error': 'This item is no longer available for purchase'
            }, status=400)

        # 检查商品是否已在购物车中
        existing_cart_items = ShoppingCart.objects.filter(
            customer=customer,
            item=item
        )

        cart_item = existing_cart_items.first()

        if cart_item:
            return JsonResponse({
                'success': False,
                'error': 'This item is already in your cart'
            }, status=400)
        
        # 创建新的购物车项
        new_cart_item = ShoppingCart.objects.create(
            customer=customer,
            item=item,
            price_at_add=item.retail_price
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def remove_from_cart(request, cart_item_id):
    """从购物车中移除商品"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)

    try:
        # 检查用户是否有customer对象
        if not hasattr(request.user, 'customer'):
            return JsonResponse({
                'success': False,
                'error': 'User does not have a customer profile'
            }, status=400)
        
        with transaction.atomic():
            # 获取要删除的购物车项
            try:
                cart_item = ShoppingCart.objects.select_related('item__location').get(
                    id=cart_item_id,
                    customer=request.user.customer
                )
            except ShoppingCart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Cart item not found or does not belong to you'
                }, status=404)
            
            # 保存位置ID，因为删除后无法再获取
            location_id = cart_item.item.location.id
            
            # 删除购物车项
            cart_item.delete()
            
            # 获取更新后的购物车信息
            cart_items = ShoppingCart.objects.filter(
                customer=request.user.customer
            )
            
            # 计算该位置的总价
            location_items = cart_items.filter(item__location_id=location_id)
            location_total = sum(item.price_at_add for item in location_items)
            
            # 获取该位置的销售税率
            try:
                location = Location.objects.get(id=location_id)
                sales_tax = location_total * location.sales_tax_rate
            except Location.DoesNotExist:
                sales_tax = 0
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart successfully',
                'cart_count': cart_items.count(),
                'location_total': float(location_total),
                'sales_tax': float(sales_tax)
            })
            
    except Exception as e:
        # 记录详细的错误信息
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing item from cart: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': f'Failed to remove item from cart: {str(e)}'
        }, status=500)

@login_required
def get_addresses(request):
    try:
        addresses = CustomerAddress.objects.filter(
            customer=request.user.customer,
            is_verified=True
        ).values('id', 'formatted_address')
        
        return JsonResponse(list(addresses), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def geocode_address(request):
    """处理地址地理编码请求"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        address_id = request.POST.get('address_id')
        if not address_id:
            return JsonResponse({'error': 'Address ID is required'}, status=400)
        
        # 获取地址
        address = CustomerAddress.objects.get(id=address_id, customer=request.user.customer)
        address_str = f"{address.street_address}, {address.city}, {address.state} {address.zip_code}"
        
        # 使用服务器端 API 进行地理编码
        if gmaps:
            geocode_result = gmaps.geocode(address_str)
        else:
            geocode_result = []
        
        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]['geometry']['location']
            return JsonResponse({
                'success': True,
                'location': location
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No results found'
            }, status=404)
            
    except CustomerAddress.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ShowMapView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/show_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        address_id = self.request.GET.get('address_id')

        if address_id:
            try:
                address = CustomerAddress.objects.get(
                    id=address_id,
                    customer=self.request.user.customer
                )
                context['address'] = address
            except CustomerAddress.DoesNotExist:
                raise Http404("Address not found")
        
        context['GOOGLE_MAPS_CLIENT_API_KEY'] = settings.GOOGLE_MAPS_CLIENT_API_KEY
        return context
    
@login_required
@require_http_methods(["POST"])
@transaction.atomic  # 确保整个操作在事务中进行
def create_order(request):
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        shipping_address_id = data.get('shipping_address_id')
        inventory_items_data = data.get('inventory_items', [])
        
        if not location_id or not inventory_items_data:
            raise Exception('Missing required parameters')

        # 创建BaseCompanyMixin实例来获取过滤后的查询集
        company_mixin = BaseCompanyMixin()
        location = company_mixin.get_company_filtered_locations().get(id=location_id)
        company_id = location.company_id
            
        # 获取所有商品
        inventory_item_ids = [item['inventory_item_id'] for item in inventory_items_data]
        
        inventory_items = company_mixin.get_company_filtered_inventory_items().filter(
            id__in=inventory_item_ids
        ).select_related('current_state')
        
        if len(inventory_items) != len(inventory_item_ids):
            raise Exception('Some inventory items not found')
            
        # 步骤0：校验所有商品的状态
        try:
            hold_state = ItemState.objects.get(name='HOLD')
        except ItemState.DoesNotExist:
            raise Exception('HOLD state not found in system')
            
        for item in inventory_items:
            if item.current_state == hold_state:
                raise Exception(f'Item {item.control_number} is already on hold')
                
            # 检查状态转换是否合法
            try:
                state_transition = StateTransition.objects.get(
                    from_state=item.current_state,
                    to_state=hold_state
                )
            except StateTransition.DoesNotExist:
                raise Exception(f'Item {item.control_number} cannot be put on hold')
        
        # 步骤1：创建订单
        # 使用order app中的订单编号生成函数
        # order_number = generate_order_number(location)
        order_number = None
        # 获取配送地址
        shipping_address = None
        shipping_miles = 0
        
        if shipping_address_id:
            try:
                shipping_address = CustomerAddress.objects.get(id=shipping_address_id)
                # 计算配送距离
                shipping_miles = round(geodesic(
                    (shipping_address.latitude, shipping_address.longitude),
                    (location.address.latitude, location.address.longitude)
                ).miles, 1)
            except CustomerAddress.DoesNotExist:
                pass
        
        order = Order.objects.create(
            order_number=order_number if order_number else None,
            company_id=company_id,
            customer=request.user.customer,
            location_id=location_id,
            created_by=request.user,
            order_status='PENDING',
            payment_status='NOT_PAID',
            total_amount=0,
            tax_amount=0,
            shipping_amount=0,
            taxable_amount=0,
            non_taxable_amount=0,
            shipping_address=shipping_address.get_full_address() if shipping_address else None,
            shipping_miles=shipping_miles,
            receiver_name=request.user.get_full_name(),
            receiver_phone=request.user.customer.phone,
            receiver_email=request.user.email,
            notes=None
        )
        
        # 创建订单状态历史记录
        OrderStatusHistory.objects.create(
            order=order,
            from_status=None,
            to_status='PENDING',
            changed_by=request.user.staff if hasattr(request.user, 'staff') else None,
            notes='Customer create order from shopping cart' if not hasattr(request.user, 'staff') else 'Staff create order from dashboard'
        )
        
        # 步骤2：创建订单项目并更新库存状态
        for item_data in inventory_items_data:
            try:
                item = next(i for i in inventory_items if i.id == item_data['inventory_item_id'])
                
                # 更新库存项目，将其关联到订单
                item.order = order
                item.unit_price = Decimal(str(item_data['unit_price']))  # 确保转换为Decimal
                item.save()
            
            except Exception as e:
                raise Exception(f"处理商品时出错: {str(e)}")
            
            # 先获取状态转换规则
            try:
                state_transition = StateTransition.objects.get(
                    from_state=item.current_state,
                    to_state=hold_state
                )
            except StateTransition.DoesNotExist:
                raise Exception(f'Invalid state transition for item {item.control_number}')
            
            # 创建状态历史记录
            InventoryStateHistory.objects.create(
                inventory_item=item,
                state_transition=state_transition,
                changed_by=request.user.staff if hasattr(request.user, 'staff') else None,
                notes='Customer created Order'
            )
            
            # 最后更新库存状态为HOLD
            item.current_state = hold_state
            item.save()
            
            # 验证订单项目创建是否成功
            if not InventoryItem.objects.filter(
                order=order,
                unit_price=Decimal(str(item_data['unit_price']))
            ).exists():
                raise Exception(f"Failed to create order item for {item.control_number}")
        
        # 删除这些商品的购物车记录
        ShoppingCart.objects.filter(
            customer=request.user.customer,
            item__in=inventory_items
        ).delete()
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'redirect_url': reverse('frontend:customer_dashboard')
        })
        
    except Exception as e:
        # 确保事务回滚
        transaction.set_rollback(True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    

class CustomerOrderDetailView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    template_name = 'frontend/customer_order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = self.kwargs.get('order_number')
        
        # 先通过订单号找到订单，获取订单ID，只显示配置公司的订单
        order = get_object_or_404(
            self.get_company_filtered_orders().select_related(
                'customer', 'customer__user', 'location', 'location__address', 'company'
            ),
            order_number=order_number,
            customer=self.request.user.customer  # 确保订单属于当前用户
        )
        
        # 使用订单ID进行所有后续的数据库查询
        order_id = order.id
        
        # 获取订单项目 - 使用订单ID
        order_items = order.inventory_items.all().select_related(
            'model_number',
            'model_number__brand',
            'model_number__category',
            'current_state'
        )
        
        # 为每个订单项目加载图片数据
        for item in order_items:
            # 按需加载图片：如果商品有图片则加载商品图片，否则加载产品型号图片
            if item.images.exists():
                # 商品有图片，加载第一张商品图片
                item_images = ItemImage.objects.filter(
                    item=item
                ).only('image').order_by('display_order')[:1]
                item.item_images = list(item_images)
            else:
                # 商品没有图片，加载第一张产品型号图片
                model_images = ProductImage.objects.filter(
                    product_model=item.model_number
                ).only('image').order_by('id')[:1]
                item.item_images = list(model_images)
        
        # 获取交易记录 - 使用订单ID
        transaction_records = TransactionRecord.objects.filter(
            customer=order.customer,
            company=order.company,
            order_id=order_id  # 使用订单ID而不是订单对象
        ).order_by('created_at')
        
        # 计算当前余额
        current_balance = order.calculate_order_balance()
        
        # 计算时间差
        now = timezone.now()
        time_diff = now - order.created_at
        
        # 计算总秒数
        total_seconds = time_diff.total_seconds()
        
        # 计算天数、小时和分钟
        days = int(total_seconds // (24 * 3600))
        remaining_seconds = total_seconds % (24 * 3600)
        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)
        
        # 构建时间显示字符串
        time_since_creation = []
        if days > 0:
            time_since_creation.append(f"{days} Days")
        if hours > 0:
            time_since_creation.append(f"{hours} Hours")
        if minutes > 0:
            time_since_creation.append(f"{minutes} Minutes")
        time_since_creation_str = " ".join(time_since_creation)
        
        # 计算税前总价
        pre_tax_amount = order.calculate_pre_tax_total()
        
        # 检查保修政策和条款条件同意状态
        warranty_agreed = False
        terms_agreed = False
        
        if self.request.user.is_authenticated:
            try:
                customer = self.request.user.customer
                location = order.location
                
                # 检查保修政策同意状态
                warranty_agreed = CustomerWarrantyPolicy.has_agreed(customer, location)
                
                # 检查条款和条件同意状态
                terms_agreed = CustomerTermsAgreement.has_agreed(customer, location)
                
            except Exception:
                # 如果获取用户信息失败，保持默认值False
                pass
        
        context.update({
            'order': order,
            'order_items': order_items,
            'transaction_records': transaction_records,
            'current_balance': current_balance,
            'company_name': order.company.company_name,
            'location_name': order.location.name,
            'location_address': order.location.address.get_full_address(),
            'location_timezone': order.location.timezone,
            'time_since_creation': time_since_creation_str,
            'shipping_distance': f"{order.shipping_miles:.1f} miles" if order.shipping_miles else None,
            'pre_tax_amount': pre_tax_amount,
            'warranty_agreed': warranty_agreed,
            'terms_agreed': terms_agreed,
            'location': order.location,  # 添加location对象用于URL生成
            'GOOGLE_MAPS_CLIENT_API_KEY': settings.GOOGLE_MAPS_CLIENT_API_KEY
        })
        return context

    def post(self, request, *args, **kwargs):
        """处理替代联系人和地址信息的更新"""
        try:
            order_number = self.kwargs.get('order_number')
            address_validator = AddressValidator(settings.GOOGLE_MAPS_API_KEY)  # 使用服务器端API密钥
            # 获取订单，只显示配置公司的订单
            # 创建BaseCompanyMixin实例来获取过滤后的查询集
            company_mixin = BaseCompanyMixin()
            order = get_object_or_404(
                company_mixin.get_company_filtered_orders().select_related('customer'),
                order_number=order_number,
                customer=request.user.customer
            )
            
            # 检查请求类型
            action = request.POST.get('action')
            
            if action == 'confirm_order':
                # 处理订单确认
                return self._handle_order_confirmation(request, order)
            else:
                # 处理替代联系人和地址信息更新
                return self._handle_alternative_contact_update(request, order, address_validator)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing request: {str(e)}'
            })

    def _handle_order_confirmation(self, request, order):
        """处理订单确认"""
        try:
            # 检查订单状态是否为UPDATED
            if order.order_status != 'UPDATED':
                return JsonResponse({
                    'success': False,
                    'error': 'Order can only be confirmed when status is "Updated"'
                })
            
            # 直接设置订单状态为CONFIRMED
            order.order_status = 'CONFIRMED'
            order.save()
            
            # 创建订单状态历史记录
            from .models_proxy import OrderStatusHistory
            customer_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            OrderStatusHistory.objects.create(
                order=order,
                from_status='UPDATED',
                to_status='CONFIRMED',
                changed_by=None,  # 客户确认，没有staff记录
                notes=f'Order confirmed by customer {customer_name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Order has been confirmed successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error confirming order: {str(e)}'
            })

    def _handle_alternative_contact_update(self, request, order, address_validator):
        """处理替代联系人和地址信息更新"""
        try:
            # 获取表单数据
            alternative_receiver_name = request.POST.get('alternative_receiver_name', '').strip()
            alternative_receiver_phone = request.POST.get('alternative_receiver_phone', '').strip()
            alternative_shipping_address = request.POST.get('alternative_shipping_address', '').strip()
            
            # 检查是否所有字段都为空
            if not alternative_receiver_name and not alternative_receiver_phone and not alternative_shipping_address:
                return JsonResponse({
                    'success': True,
                    'message': 'No changes to save'
                })
            
            # 验证地址（如果提供了地址）
            if alternative_shipping_address:
                try:
                    # 使用地址校验器
                    validation_result = address_validator.validate_address(alternative_shipping_address)
                    
                    if not validation_result['valid']:
                        return JsonResponse({
                            'success': False,
                            'error': f'Invalid shipping address: {validation_result["error"]}'
                        })
                    
                    # 使用验证后的格式化地址
                    alternative_shipping_address = validation_result['formatted_address']
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Address validation failed: {str(e)}'
                    })
            
            # 更新订单信息
            order.alternative_receiver_name = alternative_receiver_name or None
            order.alternative_receiver_phone = alternative_receiver_phone or None
            order.alternative_shipping_address = alternative_shipping_address or None
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Alternative contact information updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error updating information: {str(e)}'
            })

@csrf_exempt
@require_http_methods(["POST"])
def search_suggestions(request):
    """搜索建议API - 返回匹配的产品建议"""
    try:
        query = request.POST.get('query', '').strip()
        if len(query) < 2:
            return JsonResponse({'status': 'success', 'suggestions': []})
        
        # 搜索已发布的库存商品，只显示配置公司的商品
        # 创建BaseCompanyMixin实例来获取过滤后的查询集
        company_mixin = BaseCompanyMixin()
        items = company_mixin.get_company_filtered_inventory_items().select_related(
            'model_number',
            'model_number__brand',
            'model_number__category'
        ).filter(
            models.Q(model_number__brand__name__icontains=query) |
            models.Q(model_number__category__name__icontains=query) |
            models.Q(model_number__model_number__icontains=query) |
            models.Q(model_number__description__icontains=query)
        ).annotate(
            favorite_count=Count('favorited_by', distinct=True)
        ).distinct()[:10]  # 限制返回10个结果
        
        suggestions = []
        for item in items:
            # 生成商品哈希
            item_hash = get_item_hash(item)
            
            # 如果无法生成哈希，跳过这个商品
            if not item_hash:
                continue
            
            # 获取商品图片
            if item.images.exists():
                image = item.images.first().image
            elif item.model_number.images.exists():
                image = item.model_number.images.first().image
            else:
                image = None
            
            suggestion = {
                'id': item.id,
                'item_hash': item_hash,
                'brand': item.model_number.brand.name,
                'category': item.model_number.category.name,
                'model_number': item.model_number.model_number,
                'description': item.model_number.description[:100] + '...' if len(item.model_number.description) > 100 else item.model_number.description,
                'retail_price': float(item.retail_price),
                'msrp': float(item.model_number.msrp) if item.model_number.msrp else None,
                'image_url': image.url if image else None,
                'favorite_count': item.favorite_count,
                'url': reverse('frontend:item_detail', kwargs={'item_hash': item_hash})
            }
            suggestions.append(suggestion)
        
        return JsonResponse({
            'status': 'success',
            'suggestions': suggestions
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


class SearchResultsView(BaseFrontendMixin, TemplateView):
    """搜索结果页面"""
    template_name = 'frontend/search_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        
        if not query:
            context.update({
                'query': '',
                'items': [],
                'total_count': 0
            })
            return context
        
        # 搜索已发布的库存商品，且状态为可销售状态，只显示配置公司的商品
        items = self.get_company_filtered_inventory_items().filter(
            published=True,
            current_state_id__in=[4, 5, 8]  # 只显示这三种状态的商品
        ).select_related(
            'model_number',
            'model_number__brand',
            'model_number__category'
        ).filter(
            models.Q(model_number__brand__name__icontains=query) |
            models.Q(model_number__category__name__icontains=query) |
            models.Q(model_number__model_number__icontains=query) |
            models.Q(model_number__description__icontains=query)
        ).annotate(
            favorite_count=Count('favorited_by', distinct=True)
        ).distinct()
        
        # 预加载图片
        items_with_images = items.filter(images__isnull=False).prefetch_related(
            models.Prefetch(
                'images',
                queryset=ItemImage.objects.only('image').order_by('display_order')[:1],
                to_attr='item_images'
            )
        )
        
        items_without_images = items.filter(images__isnull=True).prefetch_related(
            models.Prefetch(
                'model_number__images',
                queryset=ProductImage.objects.only('image').order_by('id')[:1],
                to_attr='model_images'
            )
        )
        
        # 合并查询集
        all_items = list(items_with_images) + list(items_without_images)
        
        # 为每个商品计算节省金额和生成哈希
        valid_items = []
        for item in all_items:
            if item.model_number.msrp:
                item.savings = item.model_number.msrp - item.retail_price
                item.savings_percentage = (item.savings / item.model_number.msrp) * 100
            else:
                item.savings = 0
                item.savings_percentage = 0
            
            item.item_hash = get_item_hash(item)
            
            # 只添加能成功生成哈希的商品
            if item.item_hash:
                valid_items.append(item)
        
        context.update({
            'query': query,
            'items': valid_items,
            'total_count': len(valid_items)
        })
        
        return context


class WarrantyPolicyView(BaseFrontendMixin, TemplateView):
    """保修政策展示页面（未登录可访问）"""
    template_name = 'frontend/warranty_policy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_slug = kwargs['location_slug']
        location = get_object_or_404(
            self.get_company_filtered_locations(), 
            slug=location_slug
        )
        
        # 获取当前有效的保修政策
        warranty_policy = LocationWarrantyPolicy.get_active_policy_for_location(location)
        
        # 读取文件内容
        policy_content = None
        if warranty_policy and warranty_policy.content_file:
            try:
                with warranty_policy.content_file.open('r') as f:
                    policy_content = f.read()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading warranty policy file: {e}")
                policy_content = "Error loading policy content."
        
        # 检查用户是否已经同意（仅对已登录用户）
        has_agreed = False
        if self.request.user.is_authenticated:
            try:
                customer = self.request.user.customer
                has_agreed = CustomerWarrantyPolicy.has_agreed(customer, location)
            except Exception:
                # 如果获取客户信息失败，保持has_agreed为False
                pass
        
        context.update({
            'location': location,
            'warranty_policy': warranty_policy,
            'policy_content': policy_content,
            'is_logged_in': self.request.user.is_authenticated,
            'has_agreed': has_agreed,
        })
        return context


class WarrantyAgreementView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    """保修政策同意页面（需要登录）"""
    template_name = 'frontend/warranty_agreement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_slug = kwargs['location_slug']
        location = get_object_or_404(
            self.get_company_filtered_locations(),
            slug=location_slug
        )
        customer = self.request.user.customer

        # 获取来源参数
        source = self.request.GET.get('source', '')
        order_number = self.request.GET.get('order_number', '')

        # 获取当前有效的保修政策
        warranty_policy = LocationWarrantyPolicy.get_active_policy_for_location(location)

        # 读取文件内容
        policy_content = None
        if warranty_policy and warranty_policy.content_file:
            try:
                with warranty_policy.content_file.open('r') as f:
                    policy_content = f.read()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading warranty policy file: {e}")
                policy_content = "Error loading policy content."

        # 检查是否已经同意
        has_agreed = CustomerWarrantyPolicy.has_agreed(customer, location)

        # 检查Terms是否已同意（用于显示导航按钮）
        has_agreed_terms = CustomerTermsAgreement.has_agreed(customer, location)
        
        context.update({
            'location': location,
            'warranty_policy': warranty_policy,
            'policy_content': policy_content,
            'has_agreed': has_agreed,
            'has_agreed_terms': has_agreed_terms,
            'customer': customer,
            'source': source,
            'order_number': order_number,
        })
        return context


@require_POST
def agree_warranty_policy(request, location_slug):
    """处理保修政策同意"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    # 创建BaseCompanyMixin实例来获取过滤后的查询集
    company_mixin = BaseCompanyMixin()
    location = get_object_or_404(
        company_mixin.get_company_filtered_locations(), 
        slug=location_slug
    )
    customer = request.user.customer
    warranty_policy = LocationWarrantyPolicy.get_active_policy_for_location(location)
    
    if not warranty_policy:
        return JsonResponse({'success': False, 'error': 'No active warranty policy found'})
    
    # 创建同意记录
    CustomerWarrantyPolicy.objects.create(
        customer=customer,
        location=location,
        warranty_version=warranty_policy.version,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({'success': True, 'message': 'Warranty policy agreed successfully'})


class TermsAndConditionsView(BaseFrontendMixin, TemplateView):
    """条款和条件展示页面（未登录可访问）"""
    template_name = 'frontend/terms_conditions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_slug = kwargs['location_slug']
        location = get_object_or_404(
            self.get_company_filtered_locations(), 
            slug=location_slug
        )
        
        # 获取当前有效的条款和条件
        terms_conditions = LocationTermsAndConditions.get_active_terms_for_location(location)
        
        # 读取文件内容
        terms_content = None
        if terms_conditions and terms_conditions.content_file:
            try:
                with terms_conditions.content_file.open('r') as f:
                    terms_content = f.read()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading terms and conditions file: {e}")
                terms_content = "Error loading terms and conditions content."
        
        # 检查用户是否已经同意（仅对已登录用户）
        has_agreed = False
        if self.request.user.is_authenticated:
            try:
                customer = self.request.user.customer
                has_agreed = CustomerTermsAgreement.has_agreed(customer, location)
            except Exception:
                # 如果获取客户信息失败，保持has_agreed为False
                pass
        
        context.update({
            'location': location,
            'terms_conditions': terms_conditions,
            'terms_content': terms_content,
            'is_logged_in': self.request.user.is_authenticated,
            'has_agreed': has_agreed,
        })
        return context


class TermsAgreementView(LoginRequiredMixin, BaseFrontendMixin, TemplateView):
    """条款和条件同意页面（需要登录）"""
    template_name = 'frontend/terms_agreement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_slug = kwargs['location_slug']
        location = get_object_or_404(
            self.get_company_filtered_locations(),
            slug=location_slug
        )
        customer = self.request.user.customer

        # 获取来源参数
        source = self.request.GET.get('source', '')
        order_number = self.request.GET.get('order_number', '')

        # 获取当前有效的条款和条件
        terms_conditions = LocationTermsAndConditions.get_active_terms_for_location(location)

        # 读取文件内容
        terms_content = None
        if terms_conditions and terms_conditions.content_file:
            try:
                with terms_conditions.content_file.open('r') as f:
                    terms_content = f.read()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading terms and conditions file: {e}")
                terms_content = "Error loading terms and conditions content."

        # 检查是否已经同意
        has_agreed = CustomerTermsAgreement.has_agreed(customer, location)

        # 检查Warranty是否已同意（用于显示导航按钮）
        has_agreed_warranty = CustomerWarrantyPolicy.has_agreed(customer, location)
        
        context.update({
            'location': location,
            'terms_conditions': terms_conditions,
            'terms_content': terms_content,
            'has_agreed': has_agreed,
            'has_agreed_warranty': has_agreed_warranty,
            'customer': customer,
            'source': source,
            'order_number': order_number,
        })
        return context


@require_POST
def agree_terms_conditions(request, location_slug):
    """处理条款和条件同意"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    # 创建BaseCompanyMixin实例来获取过滤后的查询集
    company_mixin = BaseCompanyMixin()
    location = get_object_or_404(
        company_mixin.get_company_filtered_locations(), 
        slug=location_slug
    )
    customer = request.user.customer
    terms_conditions = LocationTermsAndConditions.get_active_terms_for_location(location)
    
    if not terms_conditions:
        return JsonResponse({'success': False, 'error': 'No active terms and conditions found'})
    
    # 创建同意记录
    CustomerTermsAgreement.objects.create(
        customer=customer,
        location=location,
        terms_version=terms_conditions.version,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({'success': True, 'message': 'Terms and conditions agreed successfully'})


def robots_txt(request):
    """
    动态生成robots.txt文件
    基于实际sitemap配置和环境设置自动生成
    """
    # 动态获取协议和域名
    protocol = 'https' if not settings.DEBUG else 'http'
    domain = request.get_host()
    base_url = f"{protocol}://{domain}"

    # 动态生成sitemap列表
    sitemap_lines = []
    sitemap_lines.append(f"Sitemap: {base_url}/sitemap.xml")

    # 如果不是www域名，添加www版本的主sitemap
    if 'www.' not in domain:
        sitemap_lines.append(f"Sitemap: {protocol}://www.{domain}/sitemap.xml")

    # 根据实际sitemap配置字典自动生成子sitemap列表
    for section_name in sitemaps.keys():
        sitemap_lines.append(f"Sitemap: {base_url}/sitemap-{section_name}.xml")

    # 生成sitemap部分的内容
    sitemaps_section = "\n".join(sitemap_lines)

    # 动态获取所有活跃店面
    from .models import Location
    active_stores = Location.objects.filter(
        location_type='STORE',
        is_active=True
    ).exclude(slug__isnull=True).exclude(slug__exact='')

    # 生成店面Allow规则
    store_allows = []
    store_warranty_allows = []
    store_terms_allows = []
    store_names = []
    for store in active_stores:
        store_allows.append(f"Allow: /{store.slug}/")
        store_warranty_allows.append(f"Allow: /{store.slug}/warranty/")
        store_terms_allows.append(f"Allow: /{store.slug}/terms/")
        store_names.append(store.slug)

    store_allows_section = "\n".join(store_allows) if store_allows else "# No active stores found"
    store_warranty_section = "\n".join(store_warranty_allows) if store_warranty_allows else ""
    store_terms_section = "\n".join(store_terms_allows) if store_terms_allows else ""
    store_list = ", ".join(store_names) if store_names else "none"

    # 环境信息（用于调试）
    env_info = f"DEBUG={settings.DEBUG}, DOMAIN={domain}, PROTOCOL={protocol}"
    sitemap_keys = ", ".join(sitemaps.keys())

    robots_content = f"""# Appliances 4 Less Doraville - 动态生成 Robots.txt
# 环境信息: {env_info}
# 配置的Sitemap: {sitemap_keys}
# 活跃店面: {store_list}

User-agent: *

# === 核心SEO页面 - 最高优先级 ===
Allow: /
Allow: /incoming-inventory/          # 即将到货页面
{store_allows_section}              # 具体店面页面（从数据库动态获取）
Allow: /category/
Allow: /item/
Allow: /search/
Allow: /services/                    # SEO服务页面
Allow: /products/                    # 产品SEO页面

# === 法律和政策页面 - SEO友好 ===
Allow: /privacy-policy/              # 网站级政策（合规必需，SEO价值低）
Allow: /terms-of-service/            # 网站级政策（合规必需，SEO价值低）
Allow: /cookie-policy/               # 网站级政策（合规必需，SEO价值低）
# 店铺级保修和条款页面（基于具体店面）
{store_warranty_section}          # 保修政策页面
{store_terms_section}          # 条款条件页面

# === 静态资源 - 必须允许 ===
Allow: /static/
Allow: /media/
Allow: /favicon.ico

# === 严格禁止的私密区域 ===
Disallow: /customer/dashboard/       # 客户面板
Disallow: /customer/profile/         # 个人资料
Disallow: /customer/favorites/       # 收藏夹
Disallow: /customer/order/           # 订单详情

# === 购物流程页面 - 保护用户隐私 ===
Disallow: /cart/                     # 购物车
Disallow: /cart/add/                 # 添加到购物车
Disallow: /cart/remove/              # 移除商品
Disallow: /cart/calculate-distances/ # 距离计算

# === API 接口 - 防止滥用 ===
Disallow: /api/                      # 所有API
Disallow: /api/search-suggestions/   # 搜索建议API
Disallow: /api/addresses/            # 地址API
Disallow: /api/geocode-address/      # 地理编码API
Disallow: /api/orders/               # 订单API

# === 功能性页面 - 无SEO价值 ===
Disallow: /item/*/favorite/          # 收藏功能
Disallow: /show-map/                 # 地图展示
Disallow: /*/warranty/agree/         # 保修协议页面
Disallow: /*/terms/agree/            # 条款协议页面

# === 避免重复内容和无用参数 ===
Disallow: /*?q=*&page=              # 搜索分页
Disallow: /*?sort=*                 # 排序参数
Disallow: /*?filter=*               # 过滤参数
Disallow: /*?utm_*                  # 跟踪参数
Disallow: /*?ref=*                  # 推荐参数
Disallow: /*?debug=*                # 调试参数
Disallow: /*&page=                  # 分页参数
Disallow: /*?page=*&*               # 复杂分页参数

# === 管理和后台 - 绝对禁止 ===
Disallow: /admin/
Disallow: /dashboard/
Disallow: /accounts/
Disallow: /staff/
Disallow: /employee/

# === Google专项优化 ===
User-agent: Googlebot
Allow: /
Allow: /incoming-inventory/          # 即将到货页面
{store_allows_section}              # 具体店面页面
Allow: /category/
Allow: /item/
Allow: /search/
Allow: /services/                    # SEO服务页面
Allow: /products/                    # 产品SEO页面
Allow: /static/frontend/images/      # 产品图片
Allow: /media/                       # 媒体图片
Crawl-delay: 1

# === Google图片搜索优化 ===
User-agent: Googlebot-Image
Allow: /static/frontend/images/
Allow: /media/
Disallow: /media/private/
Disallow: /media/customer/

# === Bing搜索引擎优化 ===
User-agent: bingbot
Allow: /
Allow: /incoming-inventory/          # 即将到货页面
{store_allows_section}              # 具体店面页面
Allow: /category/
Allow: /item/
Allow: /search/
Allow: /services/                    # SEO服务页面
Allow: /products/                    # 产品SEO页面
Crawl-delay: 1

# === 购物比较网站 ===
User-agent: Slurp
Allow: /item/
Allow: /category/
Allow: /services/                    # SEO服务页面
Allow: /products/                    # 产品SEO页面
Allow: /static/frontend/images/
Crawl-delay: 2

# === 屏蔽恶意爬虫 ===
User-agent: AhrefsBot
Disallow: /

User-agent: MJ12bot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: dotbot
Disallow: /

# === XML网站地图 - 动态生成 ===
{sitemaps_section}

# === 全局爬取设置 ===
Crawl-delay: 1"""

    return HttpResponse(robots_content, content_type='text/plain; charset=utf-8')


# 导入sitemap配置
from .sitemaps import (
    StaticViewSitemap, IncomingInventorySitemap, StoreSitemap, CategorySitemap,
    ProductSitemap, WarrantyPolicySitemap, TermsConditionsSitemap,
    SEOServiceListSitemap, ProductSEOPageSitemap
)

# 网站地图配置字典
sitemaps = {
    'static': StaticViewSitemap,
    'incoming': IncomingInventorySitemap,
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'warranty': WarrantyPolicySitemap,
    'terms': TermsConditionsSitemap,
    'seo_services': SEOServiceListSitemap,
    'seo_products': ProductSEOPageSitemap,  # 动态产品SEO页面
}

# 网站地图视图
def sitemap_view(request, section=None):
    """
    网站地图视图
    支持单个sitemap和sitemap索引
    """
    if section:
        # 单个sitemap
        if section in sitemaps:
            return sitemap(request, {section: sitemaps[section]})
        else:
            raise Http404("Sitemap section not found")
    else:
        # sitemap索引
        return sitemap(request, sitemaps)


# === SEO页面视图 ===


class SEOServiceListView(BaseFrontendMixin, TemplateView):
    """
    Service type list page
    Display services for a specific city or all services when no city is specified
    """
    template_name = 'frontend/seo_service_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        city_key = kwargs.get('city_key')
        
        # 为服务添加key字段
        services_with_keys = {}
        for service_key, service_info in SERVICE_TYPES.items():
            service_with_key = service_info.copy()
            service_with_key['key'] = service_key
            services_with_keys[service_key] = service_with_key
        
        context['services'] = services_with_keys
        
        # 如果提供了city_key，则显示城市信息
        if city_key:
            # 验证城市是否存在
            if city_key not in CITIES:
                raise Http404("城市不存在")
            
            city = CITIES[city_key].copy()  # 创建副本避免修改原始数据
            city['key'] = city_key  # 添加key字段
            
            # 获取附近城市的详细信息
            nearby_cities = []
            for nearby_city_name in city['nearby_cities']:
                # 查找对应的城市键名
                for key, city_data in CITIES.items():
                    if city_data['name'] == nearby_city_name:
                        nearby_city_info = city_data.copy()
                        nearby_city_info['key'] = key
                        nearby_cities.append(nearby_city_info)
                        break
            
            city['nearby_cities'] = nearby_cities
            context['city'] = city
        else:
            # 没有指定城市时，不显示城市信息
            context['city'] = None

        return context


# === 动态产品SEO页面视图 ===

class DynamicProductSEOView(BaseFrontendMixin, TemplateView):
    """
    动态产品SEO页面视图
    根据配置文件自动生成产品页面，支持基于库存的自动管理
    """
    template_name = 'frontend/product_seo_page.html'

    def get(self, request, seo_page_key, *args, **kwargs):
        # 获取SEO页面配置
        page_config = get_seo_page_config(seo_page_key)

        if not page_config:
            raise Http404("SEO page not found or disabled")

        # 构建产品筛选条件
        try:
            filters = build_product_filters(page_config)
        except Exception as e:
            logging.error(f"Failed to build product filters: {e}")
            raise Http404("Page configuration error")

        # 查询符合条件的库存商品
        inventory_items = self.get_company_filtered_inventory_items().filter(filters).select_related(
            'model_number',
            'model_number__category',
            'model_number__brand',
            'current_state'
        ).prefetch_related('images')

        # 为每个商品计算节省金额
        for item in inventory_items:
            if item.model_number.msrp:
                item.savings = item.model_number.msrp - item.retail_price
                item.savings_percentage = (item.savings / item.model_number.msrp) * 100
            else:
                item.savings = 0
                item.savings_percentage = 0

        # 检查库存数量是否满足要求
        item_count = inventory_items.count()
        min_inventory = page_config.get('min_inventory', 1)

        if item_count < min_inventory:
            # 库存不足，返回404或者友好的无库存页面
            raise Http404("Insufficient inventory available")

        # 准备上下文数据
        context = self.get_context_data(**kwargs)
        context.update({
            'seo_page_key': seo_page_key,
            'page_config': page_config,
            'inventory_items': inventory_items,
            'item_count': item_count,
            'city_info': self._get_city_info(page_config.get('city_key')),
            'seo_data': self._build_seo_data(page_config, item_count),
        })

        return self.render_to_response(context)

    def _get_city_info(self, city_key):
        """获取城市信息"""
        if not city_key or city_key not in CITIES:
            return None

        city_info = CITIES[city_key].copy()
        city_info['key'] = city_key

        # 获取附近城市信息
        nearby_cities = []
        for nearby_city_name in city_info.get('nearby_cities', []):
            for key, city_data in CITIES.items():
                if city_data['name'] == nearby_city_name:
                    nearby_city_info = city_data.copy()
                    nearby_city_info['key'] = key
                    nearby_cities.append(nearby_city_info)
                    break

        city_info['nearby_cities'] = nearby_cities
        return city_info

    def _build_seo_data(self, page_config, item_count):
        """构建SEO数据"""
        return {
            'title': page_config.get('title', ''),
            'meta_description': page_config.get('meta_description', ''),
            'keywords': ', '.join(page_config.get('keywords', [])),
            'h1_title': page_config.get('h1_title', page_config.get('title', '')),
            'canonical_url': self.request.build_absolute_uri(),
            'og_title': page_config.get('title', ''),
            'og_description': page_config.get('meta_description', ''),
            'og_image': page_config.get('featured_image', ''),
            'structured_data': self._build_structured_data(page_config, item_count),
        }

    def _build_structured_data(self, page_config, item_count):
        """构建结构化数据（JSON-LD）"""
        city_info = self._get_city_info(page_config.get('city_key'))

        structured_data = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": page_config.get('title', ''),
            "description": page_config.get('meta_description', ''),
            "url": self.request.build_absolute_uri(),
            "mainEntity": {
                "@type": "ItemList",
                "name": page_config.get('h1_title', ''),
                "description": page_config.get('content_description', ''),
                "numberOfItems": item_count,
            }
        }

        # 添加本地商业信息
        if city_info:
            structured_data["mainEntity"]["areaServed"] = {
                "@type": "City",
                "name": city_info['name'],
                "addressRegion": city_info['state'],
                "addressCountry": "US"
            }

        # 添加产品类别信息
        category_filters = page_config.get('filters', {}).get('category', {})
        if 'names' in category_filters:
            structured_data["mainEntity"]["itemListElement"] = []
            for category_name in category_filters['names']:
                structured_data["mainEntity"]["itemListElement"].append({
                    "@type": "Product",
                    "category": category_name,
                    "brand": "Various",
                    "offers": {
                        "@type": "AggregateOffer",
                        "availability": "https://schema.org/InStock",
                        "itemCondition": "https://schema.org/NewCondition"
                    }
                })

        return json.dumps(structured_data, ensure_ascii=False, indent=2)


# 图片处理和缩放视图
import os
from PIL import Image
from django.http import FileResponse, Http404
from django.core.cache import cache
import hashlib
import logging

logger = logging.getLogger(__name__)

class ImageResizeView(View):
    """
    动态图片缩放视图
    URL格式：/media/resize/{width}x{height}/{image_path}
    """

    def get(self, request, width, height, image_path):
        """处理图片缩放请求"""
        try:
            # 验证尺寸参数
            width = int(width)
            height = int(height)

            # 限制缩略图最大尺寸防止滥用（原图可以任意大小）
            if width > 1200 or height > 1200:
                return Http404("Requested thumbnail size too large")

            # 构建原图路径
            original_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # 检查原图是否存在
            if not os.path.exists(original_path):
                raise Http404("Original image not found")

            # 构建缓存路径
            cache_dir = os.path.join(settings.MEDIA_ROOT, 'cache', f'{width}x{height}')
            os.makedirs(cache_dir, exist_ok=True)

            # 生成缓存文件名（WebP格式）
            cache_filename = self._get_cache_filename(image_path, width, height)
            cache_path = os.path.join(cache_dir, cache_filename)

            # 如果缓存存在且比原图新，直接返回
            if os.path.exists(cache_path) and os.path.getmtime(cache_path) >= os.path.getmtime(original_path):
                return self._serve_image(cache_path)

            # 缓存不存在或过期，生成新的缩略图
            resized_path = self._create_resized_image(original_path, cache_path, width, height)

            return self._serve_image(resized_path)

        except (ValueError, OSError) as e:
            logger.error(f"Error processing image resize request: {e}")
            raise Http404("Invalid request")

    def _get_cache_filename(self, image_path, width, height):
        """生成缓存文件名"""
        # 使用原文件名和尺寸生成唯一的缓存文件名
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        return f"{base_name}_{width}x{height}.webp"

    def _create_resized_image(self, original_path, cache_path, width, height):
        """创建缩放后的图片"""
        try:
            # 打开原图
            with Image.open(original_path) as img:
                # 处理EXIF方向信息（修正手机拍照旋转问题）
                try:
                    from PIL import ImageOps
                    # 使用ImageOps.exif_transpose自动修正方向
                    img = ImageOps.exif_transpose(img)
                except (AttributeError, ImportError):
                    # 如果不支持exif_transpose，使用手动方法
                    try:
                        exif = img._getexif()
                        if exif is not None:
                            # EXIF方向标签的值是274
                            orientation = exif.get(274)
                            if orientation == 3:
                                img = img.rotate(180, expand=True)
                            elif orientation == 6:
                                img = img.rotate(270, expand=True)
                            elif orientation == 8:
                                img = img.rotate(90, expand=True)
                    except (AttributeError, KeyError, TypeError):
                        # 没有EXIF信息或处理失败，继续正常流程
                        pass

                # 转换为RGB模式（WebP需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # 计算缩放比例，保持宽高比
                img_ratio = img.width / img.height
                target_ratio = width / height

                if img_ratio > target_ratio:
                    # 图片更宽，按高度缩放
                    new_height = height
                    new_width = int(height * img_ratio)
                else:
                    # 图片更高，按宽度缩放
                    new_width = width
                    new_height = int(width / img_ratio)

                # 缩放图片
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 如果尺寸不完全匹配，进行居中裁剪
                if new_width != width or new_height != height:
                    left = (new_width - width) // 2
                    top = (new_height - height) // 2
                    right = left + width
                    bottom = top + height
                    img_resized = img_resized.crop((left, top, right, bottom))

                # 保存为WebP格式，优化压缩
                img_resized.save(
                    cache_path,
                    'WEBP',
                    quality=85,
                    optimize=True,
                    method=6  # 最佳压缩
                )

                logger.info(f"Created resized image: {cache_path}")
                return cache_path

        except Exception as e:
            logger.error(f"Error creating resized image: {e}")
            raise

    def _serve_image(self, image_path):
        """提供图片文件响应"""
        try:
            response = FileResponse(
                open(image_path, 'rb'),
                content_type='image/webp'
            )

            # 设置缓存头
            response['Cache-Control'] = 'public, max-age=31536000'  # 1年缓存
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'

            return response

        except Exception as e:
            logger.error(f"Error serving image: {e}")
            raise Http404("Image not available")


class IncomingInventoryView(BaseFrontendMixin, TemplateView):
    """即将到货的库存页面"""
    template_name = 'frontend/incoming_inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 使用与nasmaha相同的过滤逻辑
        tracking_states = [1, 2, 3]  # 追踪的状态ID

        # 获取状态为CONVERTING的LoadManifest，使用配置中的公司ID
        load_manifests = LoadManifest.objects.select_related(
            'location',
        ).filter(
            status=LoadManifest.Status.CONVERTING,
            company_id=settings.COMPANY_ID  # 使用配置中的公司ID
        ).order_by('-purchase_date', '-created_at')

        # 获取状态为CONVERTING的LoadManifest及其商品
        load_manifests = LoadManifest.objects.select_related(
            'location',
            'location__address'
        ).filter(
            status=LoadManifest.Status.CONVERTING,
            company_id=settings.COMPANY_ID
        ).order_by('location__name', '-purchase_date', '-created_at')

        loads_with_items = []
        for manifest in load_manifests:
            # 获取该批次中的库存商品
            inventory_items = InventoryItem.objects.select_related(
                'model_number__brand',
                'model_number__category',
                'location'
            ).prefetch_related(
                models.Prefetch(
                    'model_number__images',
                    queryset=ProductImage.objects.only('image').order_by('id')[:1],
                    to_attr='model_images'
                )
            ).filter(
                load_number=manifest,
                current_state_id__in=tracking_states
            )

            if inventory_items.exists():
                # 按类别分组该批次的商品
                from collections import defaultdict
                category_items = defaultdict(list)

                for item in inventory_items:
                    category = item.model_number.category
                    category_items[category].append(item)

                load_info = {
                    'manifest': manifest,
                    'location': manifest.location,
                    'category_items': dict(category_items),
                    'total_items': inventory_items.count()
                }
                loads_with_items.append(load_info)

        context.update({
            'loads_with_items': loads_with_items,
        })

        return context