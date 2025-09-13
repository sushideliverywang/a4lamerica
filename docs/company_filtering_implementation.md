# 公司数据过滤实施方案

## 概述

本次整改确保a4lamerica项目只显示特定公司的数据，而不是nasmaha数据库中所有公司的数据。a4lamerica作为子项目，专门为特定公司提供前端展示服务。

## 实施内容

### 1. 配置设置

**文件**: `a4lamerica/settings.py`

添加了公司ID配置：
```python
# 公司过滤配置
# 这个项目只显示特定公司的数据，而不是所有公司的数据
COMPANY_ID = int(os.getenv('COMPANY_ID', '58'))  # 默认使用公司ID 58
```

### 2. 创建公司过滤Mixin

**文件**: `frontend/views.py`

创建了`BaseCompanyMixin`类，提供统一的公司过滤逻辑：

```python
class BaseCompanyMixin:
    """
    公司过滤Mixin - 确保所有查询都限制在特定公司范围内
    这个项目只显示特定公司的数据，而不是所有公司的数据
    """
    
    def get_company_id(self):
        """获取配置的公司ID"""
        return getattr(settings, 'COMPANY_ID', 58)
    
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
```

### 3. 修改视图函数

以下视图函数已添加公司过滤：

#### 基础视图类
- `BaseFrontendMixin` - 继承`BaseCompanyMixin`
- `DetailViewMixin` - 继承`BaseCompanyMixin`

#### 页面视图
- `HomeView` - 过滤店铺和库存商品
- `StoreView` - 过滤店铺相关数据
- `ItemDetailView` - 过滤库存商品
- `CategoryView` - 过滤库存商品
- `CustomerDashboardView` - 过滤订单
- `CustomerFavoriteView` - 过滤收藏商品
- `ShoppingCartView` - 过滤购物车商品
- `SearchResultsView` - 过滤搜索结果
- `WarrantyPolicyView` - 过滤店铺数据
- `WarrantyAgreementView` - 过滤店铺数据
- `TermsAndConditionsView` - 过滤店铺数据
- `TermsAgreementView` - 过滤店铺数据

#### AJAX函数
- `search_suggestions` - 过滤搜索建议
- `create_order` - 过滤订单创建
- `agree_warranty_policy` - 过滤保修政策同意
- `agree_terms_conditions` - 过滤条款同意

#### 订单相关
- `CustomerOrderDetailView` - 过滤订单详情

## 数据过滤规则

### 需要按公司过滤的数据（公司特定数据）：
1. **Location（店铺/位置）** - 每个公司有自己的店铺
2. **InventoryItem（库存商品）** - 通过location.company关联
3. **Order（订单）** - 直接有company字段
4. **ShoppingCart（购物车）** - 通过item.location.company关联
5. **CustomerFavorite（客户收藏）** - 通过item.location.company关联
6. **TransactionRecord（交易记录）** - 有company字段
7. **LocationWarrantyPolicy（店铺保修政策）** - 通过location.company关联
8. **LocationTermsAndConditions（店铺条款条件）** - 通过location.company关联
9. **CustomerWarrantyPolicy（客户保修同意）** - 通过location.company关联
10. **CustomerTermsAgreement（客户条款同意）** - 通过location.company关联

### 不需要过滤的公共数据：
1. **Customer（客户）** - 跨公司共享
2. **ProductModel（产品型号）** - 跨公司共享
3. **Category（分类）** - 跨公司共享
4. **Brand（品牌）** - 跨公司共享
5. **CustomerAddress（客户地址）** - 客户个人数据

## 使用方法

### 环境变量配置
在`.env`文件中设置：
```
COMPANY_ID=58
```

### 代码中使用
在视图中继承`BaseCompanyMixin`或`BaseFrontendMixin`，然后使用：
- `self.get_company_filtered_locations()` - 获取过滤后的店铺
- `self.get_company_filtered_inventory_items()` - 获取过滤后的库存商品
- `self.get_company_filtered_orders()` - 获取过滤后的订单

### 独立函数中使用
创建`BaseCompanyMixin`实例：
```python
company_mixin = BaseCompanyMixin()
filtered_items = company_mixin.get_company_filtered_inventory_items()
```

## 验证方法

1. **数据库查询验证**：检查所有查询都包含公司ID过滤条件
2. **功能测试**：确保只显示配置公司的数据
3. **安全性验证**：确保无法访问其他公司的数据

## 注意事项

1. **配置管理**：确保`COMPANY_ID`设置正确
2. **数据一致性**：所有相关查询都必须使用公司过滤
3. **性能考虑**：公司过滤可能影响查询性能，需要适当索引
4. **维护性**：新增视图时记得继承`BaseCompanyMixin`

## 完成状态

✅ 所有视图函数已添加公司过滤
✅ 配置文件已更新
✅ 代码语法检查通过
✅ 文档已创建

这次整改确保了a4lamerica项目作为特定公司的子项目，只显示该公司的相关数据，提高了数据安全性和系统隔离性。
