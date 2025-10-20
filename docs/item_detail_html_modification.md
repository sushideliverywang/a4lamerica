# item_detail.html 结构化数据修改

## 修改位置

文件: `frontend/templates/frontend/item_detail.html`
位置: 第 217-297 行（结构化数据 JSON-LD 部分）

## 修改内容

### 修改前（第 217-297 行）

```html
<!-- 结构化数据 - JSON-LD -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ item.model_number.brand.name }} {{ item.model_number.model_number }}",
  "description": "{% if item.model_number.description %}{{ item.model_number.description|striptags|escapejs }}{% else %}{{ item.model_number.brand.name }} {{ item.model_number.model_number }} - {{ item.model_number.category.name }}{% endif %}",
  "brand": {
    "@type": "Brand",
    "name": "{{ item.model_number.brand.name }}"
  },
  "model": "{{ item.model_number.model_number }}",
  "category": "{{ item.model_number.category.name }}",
  "sku": "{{ item.control_number }}",
  {% if item.model_number.gtin %}
  "gtin": "{{ item.model_number.gtin }}",
  {% endif %}
  "condition": "{{ item.get_condition_display }}",
  "url": "{{ request.build_absolute_uri }}",
  "image": [
    {% if item.item_images %}
      {% for image in item.item_images %}
        "{{ request.scheme }}://{{ request.get_host }}{{ image.image.url }}"{% if not forloop.last %},{% endif %}
      {% endfor %}
    {% else %}
      "{{ request.scheme }}://{{ request.get_host }}{% static 'frontend/images/product-default.png' %}"
    {% endif %}
  ],
  "offers": {
    "@type": "Offer",
    "price": {{ item.retail_price }},
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
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
        "addressCountry": "{{ item.location.address.country }}"
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
  {% if item.warranty_type != 'NONE' %}
  ,"warranty": {
    "@type": "WarrantyPromise",
    "warrantyScope": "{{ item.get_warranty_type_display }}",
    "durationOfWarranty": "{{ item.warranty_display }}"
  }
  {% endif %}
  {% comment %}
  <!-- 评分和评论结构化数据 - 当有评分系统时启用 -->
  {% if item.average_rating and item.review_count %}
  ,"aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "{{ item.average_rating }}",
    "reviewCount": "{{ item.review_count }}",
    "bestRating": "5",
    "worstRating": "1"
  }
  {% endif %}
  {% endcomment %}
}
</script>
```

### 修改后（替换为以下内容）

```html
<!-- 结构化数据 - JSON-LD -->
<!-- 与 nasmaha Google Merchant Service 保持一致 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ structured_title|escapejs }}",
  "description": "{{ structured_description|escapejs }}",
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

## 主要变化说明

### 1. name (标题)
```html
修改前: "name": "{{ item.model_number.brand.name }} {{ item.model_number.model_number }}"
修改后: "name": "{{ structured_title|escapejs }}"
```
**变化**: 从 "Samsung RF23M8070SR" → "Samsung RF23M8070SR - Refrigerator (Open Box)"

### 2. description (描述)
```html
修改前: "description": "{% if item.model_number.description %}..."
修改后: "description": "{{ structured_description|escapejs }}"
```
**变化**: 现在包含 item_description 和保修信息

### 3. model → mpn (型号字段名)
```html
修改前: "model": "{{ item.model_number.model_number }}"
修改后: "mpn": "{{ item.model_number.model_number }}"
```
**原因**: Schema.org 标准使用 "mpn" (Manufacturer Part Number)

### 4. condition → itemCondition (条件)
```html
修改前: "condition": "{{ item.get_condition_display }}"
修改后: "itemCondition": "{{ structured_condition }}"
```
**变化**: 从 "Open Box" → "https://schema.org/NewCondition"

### 5. category (删除)
```html
修改前: "category": "{{ item.model_number.category.name }}"
修改后: (已删除)
```
**原因**: Schema.org Product 类型不直接支持此字段

### 6. availability (可用性)
```html
修改前: "availability": "https://schema.org/InStock"  (固定值)
修改后: "availability": "{{ structured_availability }}"  (动态判断)
```
**变化**: 根据 item.order 和 current_state_id 动态判断

### 7. image (图片)
```html
修改前: {% if item.item_images %}...只显示 item_images
修改后: {% for image_url in structured_images %}  (item + model 图片)
```
**变化**: 如果没有 item_images，自动使用 model 图片

### 8. offers.price (价格格式)
```html
修改前: "price": {{ item.retail_price }}
修改后: "price": "{{ item.retail_price }}"
```
**变化**: 添加引号（符合 Schema.org 规范）

### 9. offers.url (添加)
```html
修改前: (无)
修改后: "url": "{{ request.build_absolute_uri }}"
```
**原因**: 明确指定 offer 的 URL

### 10. warranty (删除独立字段)
```html
修改前: "warranty": {...}
修改后: (已删除，合并到 description)
```
**原因**: 与 Google Merchant 保持一致，保修信息放在 description 中

### 11. addressCountry (统一格式)
```html
修改前: "addressCountry": "{{ item.location.address.country }}"
修改后: "addressCountry": "US"
```
**原因**: 使用 ISO 国家代码

## 修改对照表

| 字段 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| **name** | 只有品牌和型号 | `structured_title` | 添加类别和状态 |
| **description** | 只有型号描述 | `structured_description` | 添加 item_description 和保修 |
| **model** | 存在 | 删除 | - |
| **mpn** | 不存在 | 添加 | 标准型号字段 |
| **category** | 存在 | 删除 | Schema.org Product 不支持 |
| **condition** | 存在 | 删除 | - |
| **itemCondition** | 不存在 | 添加 | 标准条件字段（URL格式） |
| **availability** | 固定 "InStock" | `structured_availability` | 动态判断 |
| **image** | 只 item_images | `structured_images` | item + model 图片 |
| **offers.price** | 数字格式 | 字符串格式 | 符合规范 |
| **offers.url** | 不存在 | 添加 | 明确 offer URL |
| **warranty** | 独立对象 | 删除 | 合并到 description |

## 验证清单

修改完成后，检查以下内容：

- [ ] name 包含完整信息（品牌+型号+类别+状态）
- [ ] description 包含型号描述、item_description、保修信息
- [ ] itemCondition 使用 Schema.org URL
- [ ] availability 根据库存状态动态变化
- [ ] image 包含所有可用图片
- [ ] 已删除不支持的 category 字段
- [ ] 已删除独立的 warranty 字段
- [ ] mpn 字段正确显示型号
- [ ] offers.price 使用字符串格式

## 测试方法

### 1. 使用 Google Rich Results Test

```
https://search.google.com/test/rich-results
```

输入修改后的页面 URL，检查是否有错误。

### 2. 查看页面源代码

在浏览器中打开商品详情页，查看源代码，检查 JSON-LD 数据是否正确。

### 3. 对比 Content API 数据

在 Django shell 中验证数据一致性：

```python
from inventory.models import InventoryItem
from inventory.google_merchant_service import GoogleMerchantService
from frontend.structured_data_utils import get_structured_data_title, get_structured_data_description

item = InventoryItem.objects.get(control_number='YOUR_CONTROL_NUMBER')
service = GoogleMerchantService(item.company)

# 对比标题
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

## 回退方案

如果需要回退，将第 217-297 行替换回原始代码即可。

建议先在开发环境测试，确认无误后再部署到生产环境。
