# A4L America - GTIN字段添加到结构化数据

**日期**: 2025-10-11
**目的**: 为商品结构化数据添加GTIN（全球贸易项目代码）字段，以增强Google Merchant Center和搜索引擎的商品识别能力

---

## 背景

GTIN（Global Trade Item Number）是产品的全球唯一标识符，包括：
- **UPC**: 12位数字（北美常用）
- **EAN**: 13位数字（国际通用）

Google Merchant Center要求产品必须提供GTIN以便于：
1. 准确识别产品
2. 提高搜索匹配度
3. 增强富媒体卡片展示
4. 改善产品可发现性

---

## 实施内容

### 1. 更新模型代理 (`frontend/models_proxy.py`)

在 `ProductModel` 类中添加 `gtin` 字段：

```python
class ProductModel(models.Model):
    # ... 其他字段 ...
    link = models.URLField(max_length=500, null=True, blank=True, verbose_name="Product URL")
    gtin = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        verbose_name="GTIN (UPC/EAN)",
        help_text="Global Trade Item Number - UPC (12 digits) or EAN (13 digits)"
    )

    class Meta:
        managed = False
        db_table = 'product_productmodel'
```

**说明**:
- `max_length=14`: 支持最长的GTIN格式（GTIN-14）
- `null=True, blank=True`: 允许为空（可选字段）
- 字段连接到nasmaha数据库的 `product_productmodel` 表

---

### 2. 更新商品详情页模板 (`frontend/templates/frontend/item_detail.html`)

在Product结构化数据中添加gtin字段：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ item.model_number.brand.name }} {{ item.model_number.model_number }}",
  "model": "{{ item.model_number.model_number }}",
  "category": "{{ item.model_number.category.name }}",
  "sku": "{{ item.control_number }}",
  {% if item.model_number.gtin %}
  "gtin": "{{ item.model_number.gtin }}",
  {% endif %}
  "condition": "{{ item.get_condition_display }}",
  ...
}
</script>
```

**位置**: 第231-233行

---

### 3. 更新分类页面模板 (`frontend/templates/frontend/category.html`)

在ItemList的Product结构化数据中添加gtin字段：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "mainEntity": {
    "@type": "ItemList",
    "itemListElement": [
      {% for item in current_category_items %}
      {
        "@type": "Product",
        "sku": "{{ item.control_number }}",
        {% if item.model_number.gtin %}
        "gtin": "{{ item.model_number.gtin }}",
        {% endif %}
        ...
      }
      {% endfor %}
    ]
  }
}
</script>
```

**位置**: 第96-98行

---

## 技术细节

### Schema.org Product规范

根据 [Schema.org Product](https://schema.org/Product) 规范：

- **gtin** 字段类型: Text
- **用途**: 产品的全球贸易项目代码
- **格式**:
  - GTIN-8: 8位数字
  - GTIN-12 (UPC): 12位数字
  - GTIN-13 (EAN): 13位数字
  - GTIN-14: 14位数字

### 条件渲染

使用Django模板条件判断，只在gtin存在时才输出：

```django
{% if item.model_number.gtin %}
"gtin": "{{ item.model_number.gtin }}",
{% endif %}
```

**优点**:
- 避免空值导致的JSON格式错误
- 保持向后兼容（旧产品没有gtin不会影响）
- 符合Schema.org最佳实践

---

## 与Nasmaha项目的同步

本次更新确保a4lamerica与nasmaha项目保持一致：

| 项目 | ProductModel.gtin | item_detail.html | category.html |
|------|-------------------|------------------|---------------|
| nasmaha | ✅ 已有 | ❓ 待确认 | ❓ 待确认 |
| a4lamerica | ✅ 本次添加 | ✅ 本次添加 | ✅ 本次添加 |

**注意**: 两个项目使用同一个数据库的 `product_productmodel` 表，gtin数据是共享的。

---

## 验证方法

### 1. Google结构化数据测试工具

访问 [Google富媒体搜索测试工具](https://search.google.com/test/rich-results) 进行验证：

1. 部署更新到测试/生产环境
2. 访问任意有GTIN的商品详情页
3. 复制页面URL到测试工具
4. 检查Product结构化数据中是否包含gtin字段
5. 确认无错误或警告

### 2. 本地测试

```python
# 在Django shell中测试
from frontend.models_proxy import ProductModel

# 查找有gtin的产品
products_with_gtin = ProductModel.objects.filter(gtin__isnull=False).exclude(gtin='')
print(f"有GTIN的产品数量: {products_with_gtin.count()}")

# 查看示例
if products_with_gtin.exists():
    sample = products_with_gtin.first()
    print(f"示例: {sample.brand.name} {sample.model_number}")
    print(f"GTIN: {sample.gtin}")
```

### 3. 页面源代码检查

在浏览器中：
1. 访问商品详情页
2. 右键 -> 查看页面源代码
3. 搜索 `"gtin":`
4. 确认值正确显示

---

## 预期效果

1. **Google Merchant Center**:
   - 产品更容易被准确识别
   - 提高产品Feed质量评分
   - 减少产品重复或识别错误

2. **Google搜索**:
   - 增强产品富媒体卡片展示
   - 提高搜索结果相关性
   - 可能获得更好的排名

3. **用户体验**:
   - 用户更容易找到准确的产品
   - 价格对比更精准
   - 增加商品页面流量

---

## 后续工作

### 数据填充

1. **现有产品**: 需要从nasmaha项目批量获取/填充GTIN数据
2. **新产品**: 在产品导入流程中确保GTIN字段被正确填充
3. **数据质量**: 定期检查GTIN数据的完整性和准确性

### 相关功能

可能需要在nasmaha项目中也更新结构化数据（如果尚未更新）：
- `nasmaha/inventory/templates/.../item_detail.html`
- `nasmaha/inventory/templates/.../category.html`

---

## 文件修改清单

1. ✅ `frontend/models_proxy.py` - 添加gtin字段到ProductModel
2. ✅ `frontend/templates/frontend/item_detail.html` - Product结构化数据添加gtin
3. ✅ `frontend/templates/frontend/category.html` - ItemList的Product结构化数据添加gtin
4. ✅ `docs/structured_data_gtin_update.md` - 本文档

---

## 参考资料

- [Schema.org Product](https://schema.org/Product)
- [Google Merchant Center产品数据规范](https://support.google.com/merchants/answer/7052112)
- [GTIN标准说明](https://www.gs1.org/standards/id-keys/gtin)
- [Google富媒体搜索测试工具](https://search.google.com/test/rich-results)

---

**维护人员**: Claude
**关联项目**: nasmaha
**数据库表**: `product_productmodel`
