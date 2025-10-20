# views.py 修改说明

## 修改位置

文件: `frontend/views.py`
类: `ItemDetailView`
方法: `get_context_data`

## 需要添加的导入

在文件顶部添加：

```python
from .structured_data_utils import get_all_structured_data
```

## 修改内容

在 `ItemDetailView.get_context_data` 方法的 `return context` 之前添加以下代码：

### 查找位置

找到 `ItemDetailView` 类的 `get_context_data` 方法，在方法末尾 `return context` 之前添加。

大约在第 540 行左右（具体行号可能略有不同）。

### 添加的代码

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['item']

        # ... 现有代码保持不变 ...

        # 面包屑导航
        context['breadcrumbs'] = [
            # ... 现有面包屑代码 ...
        ]

        # ========== 在这里添加以下代码 ==========

        # 添加结构化数据（与 nasmaha 的 Google Merchant Service 保持一致）
        structured_data = get_all_structured_data(item, self.request)
        context.update(structured_data)

        # ========== 添加结束 ==========

        return context
```

### 完整示例

```python
class ItemDetailView(DetailViewMixin, DetailView):
    model = InventoryItem
    template_name = 'frontend/item_detail.html'
    context_object_name = 'item'

    # ... get_queryset, get_object 方法保持不变 ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['item']

        # 按需加载图片
        if item.images.exists():
            item_images = ItemImage.objects.filter(
                item=item
            ).only('image').order_by('display_order')
            item.item_images = list(item_images)
        else:
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
            # ... 其他保修期限处理 ...

        # 判断商品状态
        is_sold = bool(item.order)
        is_not_available = item.current_state_id not in [4, 5, 8]
        is_available = not is_sold and not is_not_available

        # 检查商品是否在购物车
        is_in_cart = False
        if self.request.user.is_authenticated:
            from frontend.models import Cart
            is_in_cart = Cart.objects.filter(
                customer=self.request.user.customer_profile,
                item=item
            ).exists()

        # 获取收藏信息
        is_favorited = False
        favorite_count = 0
        if self.request.user.is_authenticated:
            from frontend.models import Favorite
            is_favorited = Favorite.objects.filter(
                customer=self.request.user.customer_profile,
                item=item
            ).exists()
            favorite_count = Favorite.objects.filter(item=item).count()

        # 查找相似商品
        similar_items = []
        if is_sold:
            # 已售出：查找同型号的其他可售商品
            similar_items = self.get_company_filtered_inventory_items().filter(
                model_number=item.model_number,
                current_state_id__in=[4, 5, 8],
                order__isnull=True,
                published=True
            ).exclude(id=item.id)[:4]
        else:
            # 未售出：查找同类别的其他商品
            similar_items = self.get_company_filtered_inventory_items().filter(
                model_number__category=item.model_number.category,
                current_state_id__in=[4, 5, 8],
                order__isnull=True,
                published=True
            ).exclude(id=item.id)[:4]

        # 面包屑导航
        context['breadcrumbs'] = [
            {'name': 'Home', 'url': reverse('frontend:home')},
            {'name': item.model_number.category.name, 'url': reverse('frontend:category', kwargs={'slug': item.model_number.category.slug})},
            {'name': f"{item.model_number.brand.name} {item.model_number.model_number}", 'url': ''}
        ]

        context.update({
            'is_sold': is_sold,
            'is_not_available': is_not_available,
            'is_available': is_available,
            'is_in_cart': is_in_cart,
            'is_favorited': is_favorited,
            'favorite_count': favorite_count,
            'similar_items': similar_items,
        })

        # ========== 添加结构化数据 ==========
        # 与 nasmaha 的 Google Merchant Service 保持一致
        structured_data = get_all_structured_data(item, self.request)
        context.update(structured_data)
        # ========== 添加结束 ==========

        return context
```

## 验证

修改后，在模板中可以使用以下变量：

```html
{{ structured_title }}          <!-- 完整标题: Brand Model - Category (Condition) -->
{{ structured_description }}    <!-- 完整描述: 型号描述 + item_description + 保修 -->
{{ structured_condition }}      <!-- Schema.org条件URL -->
{{ structured_availability }}   <!-- Schema.org可用性URL -->
{{ structured_images }}         <!-- 图片URL列表 -->
```

## 测试

在 Django shell 中测试：

```python
from frontend.views import ItemDetailView
from inventory.models import InventoryItem
from django.test import RequestFactory

# 获取一个商品
item = InventoryItem.objects.first()

# 创建模拟请求
factory = RequestFactory()
request = factory.get(f'/items/{item.id}/')
request.scheme = 'https'

# 创建视图实例
view = ItemDetailView()
view.request = request
view.kwargs = {'item_hash': 'test'}

# 获取上下文
context = view.get_context_data(object=item)

# 检查结构化数据
print(f"Title: {context['structured_title']}")
print(f"Description: {context['structured_description']}")
print(f"Condition: {context['structured_condition']}")
print(f"Availability: {context['structured_availability']}")
print(f"Images: {context['structured_images']}")
```
