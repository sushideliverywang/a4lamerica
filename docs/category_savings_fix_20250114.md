# Category页面Savings显示修复 - 2025年1月14日

## 问题描述

在分类页面（category.html）中，当类别没有子类别时，产品卡片中的"Save"信息不显示，但当类别有子类别时，Save信息正常显示。

## 问题分析

通过分析 `frontend/views.py` 中的 `CategoryView` 视图函数，发现问题出现在商品节省金额计算逻辑上：

### 有子类别的情况（正常显示）：
- 代码在第548-555行为子类别的商品计算了 `savings` 和 `savings_percentage`
- 模板可以正常显示节省信息

### 无子类别的情况（不显示）：
- 代码获取了 `current_category_items`，但**没有**为这些商品计算 `savings` 和 `savings_percentage`
- 导致模板中 `item.savings` 和 `item.savings_percentage` 属性不存在

## 解决方案

在 `CategoryView.get_context_data()` 方法中，为 `current_category_items` 添加节省金额计算逻辑：

```python
# 为当前类别的商品计算节省金额
for item in current_category_items:
    if item.model_number.msrp:
        item.savings = item.model_number.msrp - item.retail_price
        item.savings_percentage = (item.savings / item.model_number.msrp) * 100
    else:
        item.savings = 0
        item.savings_percentage = 0
```

## 修改位置

- 文件：`frontend/views.py`
- 方法：`CategoryView.get_context_data()`
- 位置：第500-507行（在合并查询集之后，检查子类别之前）

## 测试验证

修复后，无论类别是否有子类别，产品卡片都应该正确显示：
- 零售价格（retail_price）
- MSRP价格（如果存在）
- 节省金额（savings）和节省百分比（savings_percentage）

## 影响范围

- 分类页面（category.html）的当前类别商品显示
- 不影响子类别商品的显示逻辑
- 不影响其他页面的商品显示

## 代码一致性

此修复确保了分类页面与首页（HomeView）和商店页面（StoreView）的商品显示逻辑保持一致，这些页面都已经正确计算了节省金额。
