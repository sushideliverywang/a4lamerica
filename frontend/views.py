from django.shortcuts import render, get_object_or_404, redirect
from .models_proxy import (
    Location, Address, LocationWarrantyPolicy, LocationTermsAndConditions,
    InventoryItem, ItemImage, ItemState, Category, ProductModel, ProductImage,
    CustomerFavorite, ShoppingCart, CustomerWarrantyPolicy, CustomerTermsAgreement,
    Order, OrderStatusHistory, TransactionRecord, CustomerAddress, StateTransition,
    InventoryStateHistory,
    Company
)
from django.db import models
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, View
from django.http import Http404, JsonResponse
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
from .utils import decode_item_id, get_item_hash, generate_order_number
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
        return context


class DetailViewMixin(BaseCompanyMixin):
    """专门用于DetailView的Mixin，提供分类数据"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent_category_id__isnull=True)
        return context


class PrivacyPolicyView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/privacy_policy.html'

class TermsOfServiceView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/terms_of_service.html'

class CookiePolicyView(BaseFrontendMixin, TemplateView):
    template_name = 'frontend/cookie_policy.html'


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
        
        # 为每个分类获取对应的商品
        category_items = {}
        for category in context['categories']:
            # 获取当前类别及其所有子类别的商品，只显示配置公司的商品
            # 只显示状态为 WAITING FOR TESTING (4), TEST (5), FOR SALE (8) 的商品
            base_items = self.get_company_filtered_inventory_items().filter(
                models.Q(model_number__category=category) |  # 当前类别的商品
                models.Q(model_number__category__parent_category_id=category.id),  # 子类别的商品
                published=True,
                current_state_id__in=[4, 5, 8]  # 只显示这三种状态的商品
            ).select_related(
                'model_number',
                'model_number__brand',
                'model_number__category'
            ).annotate(
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
            'stores': stores,
            'category_items': category_items
        })
        return context


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
        """只获取已发布的商品，且状态为可销售状态，只显示配置公司的商品"""
        return self.get_company_filtered_inventory_items().filter(
            published=True,
            current_state_id__in=[4, 5, 8]  # 只显示这三种状态的商品
        ).select_related(
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
        
        # 初始化默认值
        context.update({
            'is_favorited': False,
            'favorite_count': 0,
            'is_in_cart': False,
            'breadcrumbs': [
                {'name': 'Home', 'url': reverse('frontend:home')},
                {'name': item.model_number.category.name, 'url': reverse('frontend:category', args=[item.model_number.category.slug])},
                {'name': item.model_number.model_number, 'url': '#'}
            ]
        })
        
        # 如果用户已登录，获取收藏和购物车状态
        if self.request.user.is_authenticated:
            try:
                customer = self.request.user.customer
                
                # 检查是否已收藏
                context['is_favorited'] = CustomerFavorite.objects.filter(
                    customer=customer,
                    item=item
                ).exists()
                
                # 获取收藏总数
                context['favorite_count'] = CustomerFavorite.objects.filter(item=item).count()
                
                # 检查是否在购物车中
                context['is_in_cart'] = ShoppingCart.objects.filter(
                    customer=customer,
                    item=item
                ).exists()
                
            except Exception:
                # 如果获取用户信息失败，保持默认值
                pass
        
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

class CustomerFavoriteView(BaseFrontendMixin, TemplateView):
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

class ShoppingCartView(BaseFrontendMixin, TemplateView):
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

class ShowMapView(BaseFrontendMixin, TemplateView):
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
        order_number = generate_order_number(location)
        
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
            order_number=order_number,
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
    

class CustomerOrderDetailView(BaseFrontendMixin, TemplateView):
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
        
        context.update({
            'location': location,
            'warranty_policy': warranty_policy,
            'policy_content': policy_content,
            'has_agreed': has_agreed,
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
        
        context.update({
            'location': location,
            'terms_conditions': terms_conditions,
            'terms_content': terms_content,
            'has_agreed': has_agreed,
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


    