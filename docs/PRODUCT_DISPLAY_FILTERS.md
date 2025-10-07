# A4LAmerica 产品展示过滤逻辑总结

## 基础过滤（所有视图共用）

### `BaseCompanyMixin.get_company_filtered_inventory_items()`
**位置**: `frontend/views.py` line 70-75

**基础过滤条件**:
```python
InventoryItem.objects.filter(
    location__company_id=self.get_company_id(),  # 只显示配置公司的商品
    published=True                                # 只显示已发布的商品
)
```

**说明**:
- `location__company_id`: 从 `settings.COMPANY_ID` 获取（通常为 1）
- `published=True`: 商品必须标记为已发布

---

## 各视图的额外过滤条件

### 1. HomeView（首页）
**位置**: `frontend/views.py` line 112-241

#### 1.1 SEO产品区域
**筛选逻辑**: line 145-147
```python
filters = build_product_filters(page_config)  # 使用配置文件的筛选条件
item_count = self.get_company_filtered_inventory_items().filter(filters).count()
```

**过滤条件**:
- 基础过滤: `published=True`, `order__isnull=True`, `company_id`
- 可选过滤: 类别（含子类别）、品牌、产品型号描述、库存条件
- 最小库存检查: `item_count >= min_inventory`

#### 1.2 特色分类区域
**筛选逻辑**: line 189-195
```python
base_items = self.get_company_filtered_inventory_items().filter(
    Q(model_number__category=category) |
    Q(model_number__category__parent_category_id=category.id),  # 包含子类别
    published=True,
    current_state_id__in=[4, 5, 8]  # 只显示可售状态
)
```

**状态说明**:
- `current_state_id=4`: 可售状态1
- `current_state_id=5`: 可售状态2
- `current_state_id=8`: 可售状态3

---

### 2. CategoryView（分类页面）
**位置**: `frontend/views.py` line 516-693

#### 2.1 当前类别商品
**筛选逻辑**: line 539-541
```python
base_items = self.get_company_filtered_inventory_items().filter(
    model_number__category=category,
    published=True
)
```

#### 2.2 子类别商品
**筛选逻辑**: line 596-598
```python
base_items = self.get_company_filtered_inventory_items().filter(
    model_number__category=subcategory,
    published=True
)
```

#### 2.3 可选店铺筛选
**筛选逻辑**: line 556-557, 613-614
```python
if store:
    base_items = base_items.filter(location=store)
```

**说明**:
- 不限制 `current_state_id`（显示所有状态）
- 不限制 `order`（显示已售和未售）
- 支持按店铺筛选（通过URL参数 `?store=store-slug`）

---

### 3. ItemDetailView（商品详情）
**位置**: `frontend/views.py` line 352-515

#### 3.1 商品查询
**筛选逻辑**: line 359-369
```python
return self.get_company_filtered_inventory_items().select_related(...)
# 移除所有限制: published=True, current_state_id__in=[4, 5, 8]
```

**说明**:
- **不限制** `published` 状态
- **不限制** `current_state_id`
- **不限制** `order` 状态
- 通过哈希ID访问，即使已下架或售出也能查看

#### 3.2 可用性判断
**逻辑**: line 437-449
```python
# 可购买
is_available = (
    item.published and
    item.current_state_id in [4, 5, 8] and
    item.order is None
)

# 已售出
is_sold = item.order is not None

# 不可用（已下架）
is_not_available = (
    not item.published and item.order is None
) or (
    item.published and item.current_state_id not in [4, 5, 8]
)
```

---

### 4. DynamicProductSEOView（SEO产品页面）
**位置**: `frontend/views.py` line 2594-2742

**筛选逻辑**: line 2610-2621
```python
filters = build_product_filters(page_config)
inventory_items = self.get_company_filtered_inventory_items().filter(filters)
```

**过滤条件**:
- 使用配置文件中的 `filters` 定义
- 通过 `build_product_filters()` 构建查询条件
- 检查库存数量: `item_count >= min_inventory`

**配置文件**: `frontend/config/product_seo_pages.py`

---

### 5. SearchResultsView（搜索结果）
**位置**: `frontend/views.py` line 1992-2069

**筛选逻辑**: 需要查看详细代码

---

### 6. IncomingInventoryView（即将到货）
**位置**: `frontend/views.py` line 2885-2950

**筛选逻辑**: line 222-241
```python
tracking_states = [1, 2, 3]  # 追踪的状态ID

load_manifests = LoadManifest.objects.filter(
    status=LoadManifest.Status.CONVERTING,
    company_id=settings.COMPANY_ID
)

inventory_items = InventoryItem.objects.filter(
    load_number=manifest,
    current_state_id__in=tracking_states
)
```

**状态说明**:
- 不要求 `published=True`
- 状态 1, 2, 3: 追踪中、待处理等状态
- LoadManifest 状态必须为 `CONVERTING`

---

## 核心过滤条件总结

### 必需条件（所有可购买商品）
```python
{
    'location__company_id': settings.COMPANY_ID,  # 公司ID
    'published': True,                             # 已发布
    'current_state_id__in': [4, 5, 8],            # 可售状态
    'order__isnull': True                          # 未售出
}
```

### 可选条件
```python
{
    'model_number__category_id__in': [...]         # 类别（含子类别）
    'model_number__brand__name__iexact': 'LG',    # 品牌
    'model_number__description__icontains': '...' # 产品描述关键字
    'location': store_object,                      # 特定店铺
    'condition__in': ['BRAND_NEW', 'OPEN_BOX']    # 库存条件
}
```

---

## 用于 Google Merchant Center 的推荐筛选条件

基于以上分析，上传到 Google Merchant Center 的商品应该满足：

```python
def should_sync_to_google_merchant(inventory_item):
    """
    判断商品是否应该同步到 Google Merchant Center
    """
    return (
        # 基础条件
        inventory_item.location.company_id == settings.COMPANY_ID and
        inventory_item.published == True and

        # 可售状态
        inventory_item.current_state_id in [4, 5, 8] and

        # 未售出
        inventory_item.order is None
    )
```

### 额外考虑
1. **价格**: `retail_price > 0`
2. **图片**: 优先同步有图片的商品
3. **描述**: `model_number.description` 不为空
4. **类别**: 某些特殊类别可能需要排除

---

## 状态ID对照表

| State ID | 状态说明 | 是否可售 | 是否显示 |
|----------|---------|---------|---------|
| 1 | 追踪中 | ❌ | 仅"即将到货" |
| 2 | 待处理 | ❌ | 仅"即将到货" |
| 3 | 处理中 | ❌ | 仅"即将到货" |
| 4 | 可售1 | ✅ | ✅ |
| 5 | 可售2 | ✅ | ✅ |
| 8 | 可售3 | ✅ | ✅ |
| 其他 | 不可售 | ❌ | 仅详情页 |

---

## 注意事项

1. **HomeView 的特色分类**使用了状态限制，而 **CategoryView** 没有
2. **ItemDetailView** 允许查看所有状态的商品（包括已售和已下架）
3. **SEO页面**的筛选条件完全由配置文件控制
4. 所有视图都强制要求 `company_id` 匹配
5. `get_company_filtered_inventory_items()` 只过滤 `published=True`，其他条件由各视图自行添加

---

## 建议的同步策略

### 实时同步触发条件
**应该同步到 Google**:
- `published` 从 False → True
- `current_state_id` 变为 4, 5, 或 8
- `order` 从有值 → None（取消订单）
- `retail_price` 更新

**应该从 Google 删除**:
- `published` 从 True → False
- `current_state_id` 不在 [4, 5, 8] 中
- `order` 从 None → 有值（已售出）
- 商品被删除

---

生成时间: 2025-01-XX
相关文件: frontend/views.py, frontend/config/product_seo_pages.py
