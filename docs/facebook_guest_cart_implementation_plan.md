# Facebook Commerce Manager 游客购物车实施方案

**项目**: a4lamerica
**日期**: 2025-01-XX
**目标**: 实现游客购物车功能，支持Facebook Commerce Manager集成

---

## 一、问题分析

### 1.1 当前系统状态

**购物车系统**:
- 仅支持已登录用户
- 数据存储在数据库表：`customer_shoppingcart`
- 视图使用 `LoginRequiredMixin` 强制登录

**商品标识符**:
- `item.id`: 数据库主键，**全局唯一**
- `control_number`: 公司内唯一标识符，**仅在company内唯一**
- `item_hash`: 基于item.id通过HMAC-SHA256生成的64位哈希，用于URL防止ID猜测

**当前问题**:
1. Facebook Commerce Manager要求checkout URL能接收游客访问
2. 当前系统强制登录才能使用购物车
3. Facebook Catalog Service中使用`control_number`作为`retailer_id`是**错误的**（不唯一）

### 1.2 Facebook Commerce Manager要求

根据Facebook开发者文档：

**Checkout URL格式**:
```
https://example.com/checkout?products=12345:3,23456:1&coupon=SUMMER20
```

**参数说明**:
- `products`: 逗号分隔的产品列表，格式为`retailer_id:quantity`
- `coupon`: 可选优惠券代码
- `cart_origin`: 来源标识（facebook/instagram/meta_shops）
- UTM参数: 用于追踪

**关键要求**:
1. Checkout URL必须是统一的endpoint
2. 必须支持guest checkout（不强制登录）
3. `retailer_id`必须与catalog中的一致且全局唯一
4. 每个产品的`url`字段是详情页（不是checkout URL）

---

## 二、解决方案架构

### 2.1 双购物车系统

| 用户类型 | 存储方式 | 数据结构 |
|---------|---------|---------|
| 已登录用户 | MySQL数据库 | `customer_shoppingcart`表 |
| 游客用户 | Django Session | `request.session['guest_cart']` |

**Session数据格式**:
```python
{
    'guest_cart': {
        '1234': {  # item.id作为key
            'price': '599.99',
            'location_id': 1,
            'added_at': '2025-01-15T10:30:00'
        },
        '5678': {
            'price': '899.99',
            'location_id': 2,
            'added_at': '2025-01-15T10:35:00'
        }
    }
}
```

### 2.2 标识符使用规范

| 场景 | 使用标识符 | 原因 |
|------|----------|------|
| Facebook `retailer_id` | `item.id` | 全局唯一，符合Facebook要求 |
| Facebook Checkout URL参数 | `item.id` | 与retailer_id一致 |
| 商品详情页URL | `item_hash` | 安全性，防止ID枚举 |
| 内部显示 | `control_number` | 人类可读 |

### 2.3 URL配置

| URL类型 | 路径 | 用途 |
|---------|------|------|
| Checkout URL | `/checkout/` | Facebook统一结账入口 |
| 商品详情页 | `/item/{hash}/` | 商品详细信息（hash） |
| 购物车页面 | `/cart/` | 查看购物车 |
| 添加到购物车 | `/cart/add/{hash}/` | 添加商品（hash） |
| 从购物车移除 | `/cart/remove/{cart_item_id}/` | 移除商品 |

---

## 三、实施步骤

### 步骤1: 修正Facebook Catalog Service的retailer_id

**问题**: 当前使用`control_number`（仅company内唯一）
**修复**: 改为使用`item.id`（全局唯一）

**文件**: `inventory/facebook_catalog_service.py`

**需要修改的位置**:
1. `_convert_item_to_product()` - line ~170
2. `sync_product()` - line ~215
3. `delete_product()` - line ~280

**修改内容**:
```python
# 修改前
retailer_id = str(item.control_number)

# 修改后
retailer_id = str(item.id)
```

---

### 步骤2: 创建Session购物车工具函数

**文件**: `frontend/cart_utils.py` (新建)

**功能**:
- `get_session_cart(request)` - 获取session购物车
- `add_to_session_cart(request, item)` - 添加商品
- `remove_from_session_cart(request, item_id)` - 移除商品
- `clear_session_cart(request)` - 清空购物车
- `get_session_cart_count(request)` - 获取商品数量
- `merge_session_cart_to_user(request, customer)` - 合并到用户购物车

**完整代码见附录A**

---

### 步骤3: 修改ShoppingCartView支持游客

**文件**: `frontend/views.py`

**修改内容**:
1. 移除`LoginRequiredMixin`
2. 修改`get_context_data()`方法，添加游客购物车逻辑
3. 返回`is_guest`标志给模板

**关键逻辑**:
- 判断用户是否登录
- 已登录：查询数据库购物车
- 游客：从session读取并构建临时`SessionCartItem`对象

**详细代码见附录B**

---

### 步骤4: 修改add_to_cart支持游客

**文件**: `frontend/views.py`

**修改内容**:
1. 移除`@login_required`装饰器
2. 添加游客逻辑分支

**详细代码见附录C**

---

### 步骤5: 修改remove_from_cart支持游客

**文件**: `frontend/views.py`

**修改内容**:
1. 移除`@login_required`装饰器
2. 添加游客逻辑分支
3. 游客使用item_id作为cart_item_id

**详细代码见附录D**

---

### 步骤6: 实现登录时合并购物车

**方案**: 使用Django信号

**文件1**: `frontend/signals.py` (新建)
```python
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart_utils import merge_session_cart_to_user

@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """用户登录时合并购物车"""
    if hasattr(user, 'customer'):
        added_count, skipped_count = merge_session_cart_to_user(request, user.customer)
        if added_count > 0:
            request.session['cart_merge_message'] = f'{added_count} items added to your cart'
```

**文件2**: `frontend/apps.py` (修改)
```python
class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'

    def ready(self):
        import frontend.signals  # 新增这行
```

---

### 步骤7: 新增Facebook Checkout View

**文件**: `frontend/views.py`

**功能**:
1. 接收Facebook传递的products参数
2. 解析格式：`item_id:quantity`
3. 清空现有购物车（Facebook最佳实践）
4. 添加商品到购物车（游客或已登录）
5. 跳转到购物车页面

**URL**: `frontend/urls.py`
```python
path('checkout/', views.FacebookCheckoutView.as_view(), name='facebook_checkout'),
```

**详细代码见附录E**

---

### 步骤8: 更新购物车模板

**文件**: `frontend/templates/frontend/shopping_cart.html`

**修改内容**:
1. 地址选择部分：仅对已登录用户显示
2. 游客显示登录提示
3. 移除按钮data属性保持兼容

**详细修改见附录F**

---

### 步骤9: 配置Django Session设置

**文件**: `a4lamerica/settings.py`

**添加配置**:
```python
# Session配置
SESSION_COOKIE_AGE = 259200  # 3天（秒）
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # 关闭浏览器后保留
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求更新过期时间
```

---

### 步骤10: 重新同步产品到Facebook Catalog

**操作**:
1. 在nasmaha后台，找到已同步的商品
2. 点击"重新同步到Facebook"
3. 验证新的retailer_id（应该是item.id）

**验证命令**:
```bash
# Django shell
from inventory.models import InventoryItem
from inventory.facebook_catalog_service import FacebookCatalogService

item = InventoryItem.objects.filter(published=True).first()
service = FacebookCatalogService(item.company)
product_data = service._convert_item_to_product(item)
print(f"Item ID: {item.id}")
print(f"Retailer ID: {product_data['retailer_id']}")
assert product_data['retailer_id'] == str(item.id)
```

---

## 四、Facebook Commerce Manager配置

### 4.1 设置Checkout URL

1. 登录 Facebook Commerce Manager
2. 选择你的Shop
3. 进入 Settings > Checkout
4. 选择 "Checkout on another website"
5. 输入：
   ```
   https://a4lamerica.com/checkout/
   ```

### 4.2 设置Policy URLs

```
Privacy Policy: https://a4lamerica.com/privacy-policy/
Return Policy: https://a4lamerica.com/return-policy/
Terms of Service: https://a4lamerica.com/terms-of-service/
```

### 4.3 验证Product URLs

每个产品的URL（自动生成）应该是：
```
https://a4lamerica.com/item/{64位hash}/
```

这个URL继续使用hash，不需要修改。

---

## 五、测试计划

### 5.1 单元测试

#### 测试1: Session购物车工具函数
```python
# 测试添加商品
from frontend.cart_utils import add_to_session_cart, get_session_cart
from inventory.models import InventoryItem
from django.test import RequestFactory

factory = RequestFactory()
request = factory.get('/')
request.session = {}

item = InventoryItem.objects.filter(published=True).first()
success, error = add_to_session_cart(request, item)
assert success == True

cart = get_session_cart(request)
assert str(item.id) in cart
```

#### 测试2: Retailer ID正确性
```python
from inventory.facebook_catalog_service import FacebookCatalogService

item = InventoryItem.objects.first()
service = FacebookCatalogService(item.company)
product_data = service._convert_item_to_product(item)

# 验证retailer_id是item.id
assert product_data['retailer_id'] == str(item.id)
assert product_data['retailer_id'] != str(item.control_number)
```

### 5.2 功能测试

#### 测试3: 游客添加商品到购物车
**步骤**:
1. 浏览器隐身模式访问网站（未登录）
2. 浏览商品，点击"Add to Cart"
3. 访问 `/cart/`
4. 验证商品显示在购物车中
5. 刷新页面，购物车仍保留

**预期结果**: ✅ 商品成功添加且保留

#### 测试4: 游客移除商品
**步骤**:
1. 继续上面的测试（游客状态，购物车有商品）
2. 点击"Remove"按钮
3. 验证商品被移除

**预期结果**: ✅ 商品成功移除

#### 测试5: 登录后合并购物车
**步骤**:
1. 游客状态添加商品A、B到购物车
2. 登录（假设已有商品C在数据库购物车）
3. 查看购物车

**预期结果**: ✅ 购物车包含A、B、C三个商品

#### 测试6: Facebook Checkout URL
**步骤**:
1. 浏览器访问（未登录）：
   ```
   https://a4lamerica.com/checkout/?products=1234:1,5678:1
   ```
   （替换1234、5678为实际的item.id）
2. 验证跳转到购物车页面
3. 验证两个商品都在购物车中

**预期结果**: ✅ 商品自动添加到购物车

#### 测试7: Facebook Checkout URL with Coupon
**步骤**:
1. 访问：
   ```
   https://a4lamerica.com/checkout/?products=1234:1&coupon=SUMMER20
   ```
2. 检查日志中是否记录了coupon

**预期结果**: ✅ 日志显示coupon被接收

### 5.3 集成测试

#### 测试8: Commerce Manager Validation Tool
**步骤**:
1. 在Facebook Commerce Manager中找到Checkout Validation Tool
2. 输入checkout URL
3. 添加测试商品
4. 提交验证

**预期结果**: ✅ Facebook验证通过

#### 测试9: Preview模式完整流程
**步骤**:
1. 将Shop设置为Preview模式
2. 从Facebook点击商品
3. 点击Checkout
4. 验证跳转到a4lamerica.com
5. 验证购物车中有商品

**预期结果**: ✅ 完整流程无错误

### 5.4 边界测试

#### 测试10: 空购物车
- 访问 `/cart/`（无商品）
- 预期：显示"Your cart is empty"

#### 测试11: 已售商品
- 游客添加商品A到购物车
- 商品A被其他用户购买（order不为null）
- 游客登录尝试合并
- 预期：商品A被跳过，显示提示

#### 测试12: 重复商品
- 游客添加商品A
- 登录（数据库购物车已有商品A）
- 预期：商品A只显示一次

#### 测试13: Session过期
- 游客添加商品
- 等待3天（session过期）
- 访问购物车
- 预期：购物车为空

---

## 六、部署检查清单

### 开发环境
- [ ] 创建 `frontend/cart_utils.py`
- [ ] 修改 `inventory/facebook_catalog_service.py` (retailer_id)
- [ ] 修改 `frontend/views.py` (ShoppingCartView, add_to_cart, remove_from_cart, FacebookCheckoutView)
- [ ] 创建 `frontend/signals.py`
- [ ] 修改 `frontend/apps.py`
- [ ] 修改 `frontend/urls.py` (添加checkout路由)
- [ ] 修改 `frontend/templates/frontend/shopping_cart.html`
- [ ] 修改 `a4lamerica/settings.py` (session配置)
- [ ] 运行所有测试
- [ ] 本地测试完整流程

### 生产环境（nasmaha后台）
- [ ] 重新同步所有已发布商品到Facebook Catalog
- [ ] 验证retailer_id已更新为item.id

### 生产环境（a4lamerica）
- [ ] 部署代码
- [ ] 重启服务器
- [ ] 验证session配置生效
- [ ] 测试游客购物车
- [ ] 测试Facebook checkout URL

### Facebook Commerce Manager
- [ ] 配置Checkout URL
- [ ] 配置Policy URLs
- [ ] 运行Validation Tool
- [ ] 测试Preview模式
- [ ] 发布Shop

---

## 七、回滚计划

如果出现问题，按以下步骤回滚：

### 代码回滚
```bash
git revert <commit-hash>
git push origin main
```

### Facebook Catalog回滚
如果retailer_id更改导致问题：
1. 修改代码恢复使用control_number
2. 重新同步所有商品
3. 注意：会导致所有商品被重新创建（可能丢失数据）

**建议**: 在小范围测试后再全量同步

---

## 八、风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Session存储压力 | 中 | 中 | 设置3天过期，定期清理 |
| Retailer ID更改导致重复 | 高 | 低 | 先小范围测试 |
| 商品状态变化 | 低 | 中 | 显示时检查状态 |
| Session劫持 | 中 | 低 | Django默认安全机制 |
| 购物车合并冲突 | 低 | 低 | 去重逻辑 |

---

## 九、附录

### 附录A: cart_utils.py完整代码

```python
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
```

### 附录B: ShoppingCartView修改（部分关键代码）

由于完整代码较长，这里只展示关键修改点：

```python
class ShoppingCartView(BaseFrontendMixin, TemplateView):  # 移除LoginRequiredMixin
    template_name = 'frontend/shopping_cart.html'

    def get_context_data(self, **kwargs):
        from .cart_utils import get_session_cart
        from decimal import Decimal

        context = super().get_context_data(**kwargs)

        # 判断用户是否登录
        if self.request.user.is_authenticated and hasattr(self.request.user, 'customer'):
            # 已登录用户 - 使用数据库购物车（保持原有逻辑）
            # ... 原有代码 ...
            context['is_guest'] = False
        else:
            # 游客用户 - 使用session购物车
            session_cart = get_session_cart(self.request)

            if not session_cart:
                context.update({
                    'location_items': {},
                    'is_guest': True,
                })
                return context

            # 获取session中的所有商品
            item_ids = [int(item_id) for item_id in session_cart.keys()]
            items = InventoryItem.objects.filter(
                id__in=item_ids
            ).select_related(
                'model_number',
                'model_number__brand',
                'location',
                'location__address'
            ).prefetch_related(
                'images',
                'model_number__images'
            )

            # 构建临时购物车对象
            class SessionCartItem:
                def __init__(self, item, price, cart_item_id):
                    self.id = cart_item_id
                    self.item = item
                    self.price_at_add = Decimal(price)
                    self.popularity_count = 0

            # 按location分组
            location_items = {}
            for item in items:
                cart_data = session_cart[str(item.id)]
                location = item.location

                if location not in location_items:
                    location_items[location] = {
                        'items': [],
                        'total_price': Decimal('0.00'),
                        'sales_tax': Decimal('0.00')
                    }

                cart_item = SessionCartItem(
                    item=item,
                    price=cart_data['price'],
                    cart_item_id=item.id
                )

                location_items[location]['items'].append(cart_item)
                location_items[location]['total_price'] += cart_item.price_at_add
                location_items[location]['sales_tax'] = (
                    location_items[location]['total_price'] * location.sales_tax_rate
                )

            context.update({
                'location_items': location_items,
                'is_guest': True,
            })

        return context
```

### 附录C: add_to_cart修改

```python
def add_to_cart(request, item_hash):  # 移除@login_required
    """添加商品到购物车（支持游客和已登录用户）"""
    from .cart_utils import add_to_session_cart

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        item = decode_item_id(item_hash)
        if not item:
            return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)

        # 检查商品可购买性
        if item.current_state_id not in [4, 5, 8] or item.order is not None:
            return JsonResponse({'success': False, 'error': 'This item is no longer available for purchase'}, status=400)

        # 判断用户是否登录
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            # 已登录用户 - 数据库购物车（保持原有逻辑）
            customer = request.user.customer

            if ShoppingCart.objects.filter(customer=customer, item=item).exists():
                return JsonResponse({'success': False, 'error': 'This item is already in your cart'}, status=400)

            ShoppingCart.objects.create(
                customer=customer,
                item=item,
                price_at_add=item.retail_price
            )

            return JsonResponse({'success': True, 'message': 'Item added to cart successfully'})

        else:
            # 游客用户 - session购物车
            success, error_msg = add_to_session_cart(request, item)

            if success:
                return JsonResponse({'success': True, 'message': 'Item added to cart successfully'})
            else:
                return JsonResponse({'success': False, 'error': error_msg}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### 附录D: remove_from_cart修改

```python
def remove_from_cart(request, cart_item_id):  # 移除@login_required
    """从购物车中移除商品（支持游客和已登录用户）"""
    from .cart_utils import remove_from_session_cart, get_session_cart

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            # 已登录用户 - 数据库购物车（保持原有逻辑）
            # ... 原有代码 ...
            pass

        else:
            # 游客用户 - session购物车
            success = remove_from_session_cart(request, cart_item_id)

            if not success:
                return JsonResponse({'success': False, 'error': 'Cart item not found'}, status=404)

            session_cart = get_session_cart(request)
            cart_count = len(session_cart)

            return JsonResponse({
                'success': True,
                'cart_count': cart_count
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

### 附录E: FacebookCheckoutView完整代码

```python
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class FacebookCheckoutView(View):
    """
    Facebook Commerce Manager Checkout Endpoint

    接收格式: /checkout/?products=1234:1,5678:1&coupon=SUMMER20
    """

    def get(self, request):
        from .cart_utils import clear_session_cart, add_to_session_cart
        from .models_proxy import InventoryItem, ShoppingCart

        # 1. 获取参数
        products_param = request.GET.get('products', '')
        coupon = request.GET.get('coupon', None)
        cart_origin = request.GET.get('cart_origin', 'unknown')

        # 记录来源
        request.session['cart_origin'] = cart_origin
        if coupon:
            request.session['fb_coupon'] = coupon
            logger.info(f"Facebook coupon received: {coupon}")

        # 2. 解析products
        if not products_param:
            messages.warning(request, 'No products specified.')
            return redirect('frontend:home')

        product_quantities = self._parse_products(products_param)

        if not product_quantities:
            messages.error(request, 'Invalid product format.')
            return redirect('frontend:home')

        # 3. 清空当前购物车
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            ShoppingCart.objects.filter(customer=request.user.customer).delete()
        else:
            clear_session_cart(request)

        # 4. 添加商品
        added_count = 0
        failed_items = []

        for item_id_str, quantity in product_quantities.items():
            try:
                item_id = int(item_id_str)
            except (ValueError, TypeError):
                continue

            success, error_msg = self._add_product_to_cart(request, item_id, quantity)

            if success:
                added_count += 1
            else:
                failed_items.append({'id': item_id, 'error': error_msg})

        # 5. 显示结果
        if added_count > 0:
            messages.success(request, f'{added_count} item(s) added to cart from Facebook!')

        if failed_items:
            for item in failed_items[:3]:
                messages.warning(request, f"Item {item['id']}: {item['error']}")

        # 6. 跳转
        return redirect('frontend:shopping_cart')

    def _parse_products(self, products_param):
        """解析products参数"""
        product_quantities = {}

        try:
            for entry in products_param.split(','):
                if ':' not in entry:
                    continue

                parts = entry.split(':')
                if len(parts) != 2:
                    continue

                item_id = parts[0].strip()
                try:
                    quantity = int(parts[1].strip())
                    if quantity > 0:
                        product_quantities[item_id] = quantity
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            logger.error(f"Error parsing products: {e}")

        return product_quantities

    def _add_product_to_cart(self, request, item_id, quantity):
        """添加商品到购物车"""
        from .cart_utils import add_to_session_cart
        from .models_proxy import InventoryItem, ShoppingCart

        try:
            item = InventoryItem.objects.select_related(
                'model_number',
                'model_number__brand',
                'location'
            ).get(id=item_id)

            # 检查可购买性
            if item.current_state_id not in [4, 5, 8] or item.order is not None:
                return False, 'No longer available'

            # 记录数量（但不使用）
            if quantity > 1:
                logger.info(f"Facebook requested quantity {quantity} for item {item_id}")

            # 添加到购物车
            if request.user.is_authenticated and hasattr(request.user, 'customer'):
                ShoppingCart.objects.create(
                    customer=request.user.customer,
                    item=item,
                    price_at_add=item.retail_price
                )
            else:
                success, error_msg = add_to_session_cart(request, item)
                if not success:
                    return False, error_msg

            return True, None

        except InventoryItem.DoesNotExist:
            return False, 'Product not found'
        except Exception as e:
            logger.error(f"Error adding item {item_id}: {e}")
            return False, str(e)
```

### 附录F: shopping_cart.html模板修改

只需修改地址选择部分（大约line 152-176）：

```html
<!-- Shipping Address Selection -->
{% if not is_guest %}
    <div class="flex flex-col space-y-2">
        <label class="text-text-secondary">Shipping Address (Optional)</label>
        <select class="location-address-select mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-secondary focus:border-secondary sm:text-sm rounded-md"
                data-location-id="{{ location.id }}">
            <option value="">No Address (Pick up at store)</option>
            {% if addresses %}
                {% for address in addresses %}
                    <option value="{{ address.id }}" {% if address.id == default_address.id %}selected{% endif %}>
                        {{ address.get_full_address }}
                    </option>
                {% endfor %}
            {% endif %}
            <option value="profile">+ Add New Address</option>
        </select>
        <a href="#" class="show-map-link text-secondary hover:text-orange-600 text-sm flex items-center"
           data-address-id="{{ default_address.id }}">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Show on Map
        </a>
    </div>
{% else %}
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <p class="text-sm text-blue-800">
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Please <a href="{% url 'accounts:login' %}?next={{ request.path }}" class="underline font-medium">login</a> to view delivery options and place orders.
        </p>
    </div>
{% endif %}
```

---

## 十、预期成果

完成本方案后：

1. ✅ 游客可以添加商品到购物车
2. ✅ 游客购物车保留3天
3. ✅ 登录时自动合并购物车
4. ✅ Facebook用户点击checkout直接跳转到购物车
5. ✅ Facebook Catalog使用正确的唯一标识符（item.id）
6. ✅ 商品详情页继续使用安全的hash URL
7. ✅ 符合Facebook Commerce Manager所有要求

---

## 十一、维护说明

### 日志监控

重点监控以下日志：
```python
# Facebook checkout接收到的参数
logger.info(f"Facebook checkout: products={products_param}, coupon={coupon}")

# 商品添加失败
logger.warning(f"Failed to add item {item_id}: {error_msg}")

# Session购物车合并
logger.info(f"Cart merged: added={added_count}, skipped={skipped_count}")
```

### 定期清理

建议设置定时任务清理过期session：
```bash
# Django management command
python manage.py clearsessions
```

### 性能监控

关注指标：
- Session存储大小
- 购物车页面加载时间
- Facebook checkout转化率

---

**文档版本**: 1.0
**最后更新**: 2025-01-XX
