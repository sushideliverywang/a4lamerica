# item_detail.html 结构化数据整改方案

## 目标

确保 a4lamerica 项目的 item_detail.html 中的 Schema.org 结构化数据与 nasmaha 项目的 google_merchant_service.py 中的产品数据结构**完全一致**，保证 Google 抓取的数据和通过 Content API 上传的数据一致。

## 问题分析

### 1. 标题 (Title/Name) - 严重不一致 ❌

**当前 (a4lamerica)**:
```html
"name": "{{ item.model_number.brand.name }} {{ item.model_number.model_number }}"
```
示例: `"Samsung RF23M8070SR"`

**应该是 (nasmaha)**:
```python
title = f"{brand} {model} - {category} ({condition})"
```
示例: `"Samsung RF23M8070SR - Refrigerator (Open Box)"`

**问题**:
- 缺少产品类别
- 缺少商品状态
- 不符合 Google Merchant 的标题格式

---

### 2. 描述 (Description) - 严重不一致 ❌

**当前 (a4lamerica)**:
```html
"description": "{% if item.model_number.description %}{{ item.model_number.description|striptags|escapejs }}{% else %}{{ item.model_number.brand.name }} {{ item.model_number.model_number }} - {{ item.model_number.category.name }}{% endif %}"
```
只包含: 型号通用描述

**应该是 (nasmaha)**:
```python
description_parts = []
# 1. 型号通用描述
if item.model_number.description:
    description_parts.append(item.model_number.description)
# 2. 单品特殊描述
if item.item_description:
    description_parts.append(item.item_description)
# 3. 保修信息
if item.warranty_type != 'NONE':
    warranty_type = item.get_warranty_type_display()
    warranty_period = item.get_warranty_period_display()
    description_parts.append(f"Warranty: {warranty_type} - {warranty_period}.")
description = " ".join(description_parts)
```

**问题**:
- 缺少 `item_description`（单品特殊说明，如外观瑕疵）
- 缺少保修信息
- 描述不完整

---

### 3. 条件 (Condition) - 格式不一致 ❌

**当前 (a4lamerica)**:
```html
"condition": "{{ item.get_condition_display }}"
```
返回: `"Brand New"`, `"Open Box"`, `"Scratch & Dent"`, `"Used - Good"`, `"Used - Fair"`

**应该是 (nasmaha)**:
```python
condition_mapping = {
    'BRAND_NEW': 'new',
    'OPEN_BOX': 'new',
    'SCRATCH_DENT': 'new',
    'USED_GOOD': 'used',
    'USED_FAIR': 'used',
}
return condition_mapping.get(item.condition, 'used')
```
返回: `"new"`, `"used"`, `"refurbished"`

**问题**:
- Schema.org 使用的是人类可读的格式
- Google Merchant 使用的是标准化格式
- 两者不一致会导致 Google 混淆

**Schema.org 规范**:
- `https://schema.org/NewCondition`
- `https://schema.org/UsedCondition`
- `https://schema.org/RefurbishedCondition`

---

### 4. 可用性 (Availability) - 逻辑不一致 ❌

**当前 (a4lamerica)**:
```html
"availability": "https://schema.org/InStock"
```
固定值，总是显示 "In Stock"

**应该是 (nasmaha)**:
```python
def _get_availability(self, item):
    if item.order:
        return 'out of stock'  # 已被订单关联
    if item.current_state_id in [4, 5, 8]:
        return 'in stock'  # Ready for sale, In storage, Online display
    return 'out of stock'
```

**问题**:
- 不反映真实库存状态
- 已售出的商品仍显示 "In Stock"
- 与实际业务逻辑不符

**Schema.org 规范**:
- `https://schema.org/InStock` - 有货
- `https://schema.org/OutOfStock` - 缺货
- `https://schema.org/PreOrder` - 预订

---

### 5. 图片处理 - 逻辑略有不同 ⚠️

**当前 (a4lamerica)**:
```html
"image": [
  {% if item.item_images %}
    {% for image in item.item_images %}
      "{{ request.scheme }}://{{ request.get_host }}{{ image.image.url }}"{% if not forloop.last %},{% endif %}
    {% endfor %}
  {% else %}
    "{{ request.scheme }}://{{ request.get_host }}{% static 'frontend/images/product-default.png' %}"
  {% endif %}
]
```

**nasmaha 逻辑**:
- 主图片: 优先 ItemImage，其次 ProductModel 图片
- 附加图片: ItemImage（跳过第一张）+ ProductModel 图片补充
- 最多 10 张附加图片

**问题**:
- a4lamerica 显示所有 item_images，但没有补充 model 图片
- 如果 item_images 为空，显示默认图片而不是 model 图片

---

## 整改方案

### 方案概述

需要在 `item_detail.html` 的视图中添加辅助函数，并在模板中使用这些函数生成与 nasmaha 一致的数据。

### 步骤 1: 在 views.py 中添加辅助函数

创建与 `google_merchant_service.py` 完全一致的数据处理函数：

```python
# frontend/views.py

def get_structured_data_title(item):
    """
    生成结构化数据标题（与 google_merchant_service._get_title 一致）
    格式: Brand Model - Category (Condition)
    """
    brand = item.model_number.brand.name
    model = item.model_number.model_number
    category = item.model_number.category.name
    condition = item.get_condition_display()

    title = f"{brand} {model} - {category} ({condition})"

    # Google限制150字符
    if len(title) > 150:
        title = title[:147] + "..."

    return title

def get_structured_data_description(item):
    """
    生成结构化数据描述（与 google_merchant_service._get_description 一致）
    包含: 型号描述 + item_description + 保修信息
    """
    description_parts = []

    # 1. 产品型号通用描述
    if item.model_number.description:
        description_parts.append(item.model_number.description)
    else:
        brand = item.model_number.brand.name
        model = item.model_number.model_number
        category = item.model_number.category.name
        condition = item.get_condition_display()
        description_parts.append(f"{brand} {model} {category}. Condition: {condition}.")

    # 2. 单个商品的特殊描述
    if item.item_description:
        description_parts.append(item.item_description)

    # 3. 保修信息
    if item.warranty_type and item.warranty_type != 'NONE':
        warranty_type = item.get_warranty_type_display()
        warranty_period = item.get_warranty_period_display()
        description_parts.append(f"Warranty: {warranty_type} - {warranty_period}.")

    return " ".join(description_parts)

def get_structured_data_condition(item):
    """
    获取结构化数据条件（与 google_merchant_service._get_condition 一致）
    返回 Schema.org 标准 URL
    """
    condition_mapping = {
        'BRAND_NEW': 'https://schema.org/NewCondition',
        'OPEN_BOX': 'https://schema.org/NewCondition',
        'SCRATCH_DENT': 'https://schema.org/NewCondition',
        'USED_GOOD': 'https://schema.org/UsedCondition',
        'USED_FAIR': 'https://schema.org/UsedCondition',
    }
    return condition_mapping.get(item.condition, 'https://schema.org/UsedCondition')

def get_structured_data_availability(item):
    """
    获取结构化数据可用性（与 google_merchant_service._get_availability 一致）
    返回 Schema.org 标准 URL
    """
    # 已被订单关联，不可售
    if item.order:
        return 'https://schema.org/OutOfStock'

    # 可售状态: 4 (Ready for sale), 5 (In storage), 8 (Online display)
    if item.current_state_id in [4, 5, 8]:
        return 'https://schema.org/InStock'

    return 'https://schema.org/OutOfStock'

def get_structured_data_images(item, request):
    """
    获取结构化数据图片列表（与 google_merchant_service 逻辑一致）
    优先 ItemImage，其次 ProductModel 图片
    """
    base_url = f"{request.scheme}://{request.get_host()}"
    images = []

    # 1. 获取所有 ItemImage
    item_images = item.images.all()
    for image in item_images:
        images.append(f"{base_url}{image.image.url}")

    # 2. 如果没有 ItemImage，使用 ProductModel 图片
    if not item_images.exists():
        model_images = item.model_number.images.all()
        for image in model_images:
            images.append(f"{base_url}{image.image.url}")

    # 3. 如果都没有，返回默认图片
    if not images:
        from django.templatetags.static import static
        images.append(f"{base_url}{static('frontend/images/product-default.png')}")

    return images
```

### 步骤 2: 在 item_detail 视图中添加上下文

```python
# frontend/views.py - item_detail 视图

def item_detail(request, item_hash):
    # ... 现有代码 ...

    context = {
        'item': item,
        # ... 其他现有字段 ...

        # 添加结构化数据字段
        'structured_title': get_structured_data_title(item),
        'structured_description': get_structured_data_description(item),
        'structured_condition': get_structured_data_condition(item),
        'structured_availability': get_structured_data_availability(item),
        'structured_images': get_structured_data_images(item, request),
    }

    return render(request, 'frontend/item_detail.html', context)
```

### 步骤 3: 修改 item_detail.html 模板

```html
<!-- item_detail.html - 结构化数据部分 -->

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ structured_title|escapejs }}",
  "description": "{{ structured_description|striptags|escapejs }}",
  "brand": {
    "@type": "Brand",
    "name": "{{ item.model_number.brand.name }}"
  },
  "mpn": "{{ item.model_number.model_number }}",
  "sku": "{{ item.control_number }}",
  {% if item.model_number.gtin %}
  "gtin": "{{ item.model_number.gtin }}",
  {% endif %}
  "itemCondition": "{{ structured_condition }}",
  "url": "{{ request.build_absolute_uri }}",
  "image": [
    {% for image_url in structured_images %}
      "{{ image_url }}"{% if not forloop.last %},{% endif %}
    {% endfor %}
  ],
  "offers": {
    "@type": "Offer",
    "price": "{{ item.retail_price }}",
    "priceCurrency": "USD",
    "availability": "{{ structured_availability }}",
    "url": "{{ request.build_absolute_uri }}",
    "seller": {
      "@type": "Organization",
      "name": "{{ item.location.name }}",
      "url": "{{ request.scheme }}://{{ request.get_host }}{% url 'frontend:store' item.location.slug %}"
      {% if item.location.address %}
      ,"address": {
        "@type": "PostalAddress",
        "streetAddress": "{{ item.location.address.street_number }} {{ item.location.address.street_name }}",
        "addressLocality": "{{ item.location.address.city }}",
        "addressRegion": "{{ item.location.address.state }}",
        "postalCode": "{{ item.location.address.zip_code }}",
        "addressCountry": "US"
      }
      {% endif %}
    }
  }
  {% if item.model_number.specs.all %}
  ,"additionalProperty": [
    {% for product_spec in item.model_number.specs.all %}
      {
        "@type": "PropertyValue",
        "name": "{{ product_spec.spec.name }}",
        "value": "{{ product_spec.value }}"
      }{% if not forloop.last %},{% endif %}
    {% endfor %}
  ]
  {% endif %}
}
</script>
```

## 修改对照表

| 字段 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| **name** | `"{{ brand }} {{ model }}"` | `"{{ structured_title }}"` | 添加类别和状态 |
| **description** | 只有型号描述 | `"{{ structured_description }}"` | 添加 item_description 和保修 |
| **condition** | `"{{ item.get_condition_display }}"` | 删除此字段 | - |
| **itemCondition** | 无 | `"{{ structured_condition }}"` | 使用标准 Schema.org URL |
| **model** | `"model": "{{ model_number }}"` | `"mpn": "{{ model_number }}"` | 字段名改为 mpn |
| **category** | `"category": "{{ category }}"` | 删除此字段 | Schema.org Product 不支持 |
| **availability** | `"https://schema.org/InStock"` | `"{{ structured_availability }}"` | 动态判断库存状态 |
| **image** | 只有 item_images | `structured_images` | 包含 item + model 图片 |
| **warranty** | 单独的 warranty 对象 | 删除，合并到 description | 与 Content API 一致 |

## 关键变化说明

### 1. Title 包含完整信息
```
修改前: "Samsung RF23M8070SR"
修改后: "Samsung RF23M8070SR - Refrigerator (Open Box)"
```

### 2. Description 完整详细
```
修改前:
"French Door refrigerator with FlexZone..."

修改后:
"French Door refrigerator with FlexZone... Minor scratches on left side panel. Warranty: Store Warranty - 90 Days."
```

### 3. Condition 使用标准格式
```
修改前: "condition": "Open Box"
修改后: "itemCondition": "https://schema.org/NewCondition"
```

### 4. Availability 动态判断
```
修改前: 固定 "https://schema.org/InStock"
修改后: 根据 item.order 和 current_state_id 动态判断
```

## 验证方法

### 1. 使用 Google Rich Results Test

```
https://search.google.com/test/rich-results
```

输入页面 URL，检查结构化数据是否正确。

### 2. 对比 Content API 数据

在 Django shell 中验证：

```python
from inventory.models import InventoryItem
from inventory.google_merchant_service import GoogleMerchantService
from frontend.views import get_structured_data_title, get_structured_data_description

item = InventoryItem.objects.get(control_number='YOUR_CONTROL_NUMBER')

# 对比标题
service = GoogleMerchantService(item.company)
merchant_title = service._get_title(item)
web_title = get_structured_data_title(item)
print(f"Merchant: {merchant_title}")
print(f"Web:      {web_title}")
print(f"Match:    {merchant_title == web_title}")

# 对比描述
merchant_desc = service._get_description(item)
web_desc = get_structured_data_description(item)
print(f"\nMerchant: {merchant_desc}")
print(f"Web:      {web_desc}")
print(f"Match:    {merchant_desc == web_desc}")
```

### 3. 检查 Google Search Console

提交 sitemap 后，在 Google Search Console 中查看：
- Enhancements → Products
- 检查是否有错误或警告

## 注意事项

1. **保持同步**: 如果修改 `google_merchant_service.py` 的逻辑，必须同步修改 `views.py` 的辅助函数

2. **HTML 转义**: description 中的 HTML 标签需要正确处理：
   - 在 Python 中使用 `strip_tags` 去除 HTML
   - 在模板中使用 `|striptags|escapejs`

3. **图片 URL**: 必须使用绝对 URL，包含完整的域名

4. **字段顺序**: Schema.org 不要求特定顺序，但建议保持一致性

5. **必填字段**: Schema.org Product 必填字段：
   - name (✅ 已修改)
   - image (✅ 已修改)
   - offers (✅ 有)

## 预期结果

修改后，Google 会看到：

1. **一致的产品标题**: 包含品牌、型号、类别和状态
2. **完整的产品描述**: 包含型号特性、单品说明、保修信息
3. **正确的商品状态**: 使用标准化的 condition 值
4. **准确的库存状态**: 反映真实的可售状态
5. **完整的图片列表**: ItemImage + Model 图片

这将提高：
- Google 搜索排名
- Rich Snippets 显示质量
- 用户点击率 (CTR)
- Google Shopping 推广效果

## 时间估算

- 修改 views.py: 30 分钟
- 修改 item_detail.html: 20 分钟
- 测试验证: 30 分钟
- **总计: 约 1.5 小时**

## 风险评估

**低风险**:
- 只修改结构化数据，不影响页面显示
- 用户体验不变
- SEO 只会改善，不会变差

**建议**:
- 在开发环境测试
- 使用 Google Rich Results Test 验证
- 逐步部署到生产环境
