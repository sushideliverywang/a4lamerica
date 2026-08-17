"""
Session购物车工具函数
用于管理游客用户的购物车数据
"""
from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def get_session_cart(request):
    """
    获取session购物车
    返回格式: {
        'item_id': {
            'price': '99.99',
            'location_id': 1,
            'added_at': '2024-01-01T12:00:00'
        }
    }
    """
    cart = request.session.get('guest_cart', {})
    return cart


def add_to_session_cart(request, item):
    """
    添加商品到session购物车

    参数:
        request: Django请求对象
        item: InventoryItem对象

    返回:
        (success: bool, error_msg: str or None)
    """
    cart = get_session_cart(request)
    item_id = str(item.id)

    # 检查是否已在购物车
    if item_id in cart:
        return False, 'This item is already in your cart'

    # 添加到购物车
    cart[item_id] = {
        'price': str(item.retail_price),  # 转为字符串存储
        'location_id': item.location.id if item.location else None,
        'added_at': timezone.now().isoformat()
    }

    request.session['guest_cart'] = cart
    request.session.modified = True
    return True, None


def remove_from_session_cart(request, item_id):
    """
    从session购物车移除商品

    参数:
        request: Django请求对象
        item_id: 商品ID（字符串或整数）

    返回:
        success: bool
    """
    cart = get_session_cart(request)
    item_id = str(item_id)

    if item_id in cart:
        del cart[item_id]
        request.session['guest_cart'] = cart
        request.session.modified = True
        return True
    return False


def clear_session_cart(request):
    """清空session购物车"""
    if 'guest_cart' in request.session:
        del request.session['guest_cart']
        request.session.modified = True


def get_session_cart_count(request):
    """获取session购物车商品数量"""
    cart = get_session_cart(request)
    return len(cart)


def merge_session_cart_to_user(request, customer):
    """
    将session购物车合并到用户数据库购物车
    登录时调用

    参数:
        request: Django请求对象
        customer: Customer对象

    返回:
        (added_count: int, skipped_count: int)
    """
    from .models_proxy import ShoppingCart, InventoryItem

    cart = get_session_cart(request)
    if not cart:
        return 0, 0

    added_count = 0
    skipped_count = 0

    for item_id, cart_data in cart.items():
        try:
            item = InventoryItem.objects.get(id=int(item_id))

            # 检查商品是否仍可购买
            if item.current_state_id not in [4, 5, 8] or item.order is not None:
                skipped_count += 1
                continue

            # 检查是否已在用户购物车
            if ShoppingCart.objects.filter(customer=customer, item=item).exists():
                skipped_count += 1
                continue

            # 添加到用户购物车
            ShoppingCart.objects.create(
                customer=customer,
                item=item,
                price_at_add=Decimal(cart_data['price'])
            )
            added_count += 1

        except (InventoryItem.DoesNotExist, ValueError, KeyError) as e:
            logger.warning(f"Error merging item {item_id}: {e}")
            skipped_count += 1
            continue

    # 清空session购物车
    clear_session_cart(request)

    return added_count, skipped_count
