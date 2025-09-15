# 网站结构化数据实现方案

## 概述

本文档描述了为整个网站添加结构化数据的完整实现方案，包括商品详情页、分类页面、店铺页面和首页，以便在 Google Search Console 中生成富媒体卡片。

## 实现的结构化数据类型

### 1. 商品详情页 (item_detail.html)

#### Product Schema (产品信息)
- **类型**: `Product`
- **包含字段**:
  - `name`: 产品名称 (品牌 + 型号)
  - `description`: 产品描述
  - `brand`: 品牌信息
  - `model`: 型号
  - `category`: 产品类别
  - `sku`: 控制编号
  - `mpn`: 制造商零件号
  - `condition`: 商品状态
  - `url`: 商品页面URL
  - `image`: 商品图片数组
  - `offers`: 价格和库存信息
  - `additionalProperty`: 技术规格
  - `warranty`: 保修信息

#### Organization Schema (店铺信息)
- **类型**: `Organization`
- **包含字段**:
  - `name`: 店铺名称
  - `url`: 店铺页面URL
  - `address`: 店铺地址
  - `logo`: 店铺标志

#### BreadcrumbList Schema (面包屑导航)
- **类型**: `BreadcrumbList`
- **包含字段**:
  - `itemListElement`: 导航项目列表
  - 每个项目包含位置、名称和URL

#### Offer Schema (价格信息)
- **类型**: `Offer`
- **包含字段**:
  - `price`: 零售价格
  - `priceCurrency`: 货币类型 (USD)
  - `availability`: 库存状态
  - `seller`: 销售商信息

### 2. 分类页面 (category.html)

#### CollectionPage Schema (分类页面信息)
- **类型**: `CollectionPage`
- **包含字段**:
  - `name`: 分类页面名称
  - `description`: 分类页面描述
  - `url`: 分类页面URL
  - `mainEntity`: 商品列表信息

#### ItemList Schema (商品列表)
- **类型**: `ItemList`
- **包含字段**:
  - `name`: 商品列表名称
  - `description`: 商品列表描述
  - `numberOfItems`: 商品数量
  - `itemListElement`: 商品列表项

#### Product Schema (商品信息)
- **类型**: `Product`
- **包含字段**: 与商品详情页相同的产品信息

#### BreadcrumbList Schema (面包屑导航)
- **类型**: `BreadcrumbList`
- **包含字段**: 支持店铺模式和普通模式的导航

### 3. 店铺页面 (store.html)

#### LocalBusiness Schema (本地商家信息)
- **类型**: `LocalBusiness`
- **包含字段**:
  - `name`: 店铺名称
  - `description`: 店铺描述
  - `url`: 店铺页面URL
  - `image`: 店铺图片
  - `address`: 店铺地址
  - `geo`: 地理位置坐标
  - `openingHoursSpecification`: 营业时间
  - `hasOfferCatalog`: 商品目录

#### BreadcrumbList Schema (面包屑导航)
- **类型**: `BreadcrumbList`
- **包含字段**: 从首页到店铺页面的导航

### 4. 首页 (home.html)

#### WebSite Schema (网站信息)
- **类型**: `WebSite`
- **包含字段**:
  - `name`: 网站名称
  - `url`: 网站URL
  - `description`: 网站描述
  - `potentialAction`: 搜索功能定义

#### Organization Schema (公司信息)
- **类型**: `Organization`
- **包含字段**:
  - `name`: 公司名称
  - `description`: 公司描述
  - `url`: 公司网站URL
  - `logo`: 公司标志
  - `contactPoint`: 联系信息
  - `hasOfferCatalog`: 商品目录

#### LocalBusiness Schema (所有店铺信息)
- **类型**: `LocalBusiness`
- **包含字段**: 每个店铺的详细信息

## 技术实现细节

### 模板过滤器
添加了 `add_days` 过滤器用于计算价格有效期：
```python
@register.filter
def add_days(date, days):
    """为日期添加指定天数"""
    try:
        if hasattr(date, 'date'):
            date_obj = date.date()
        else:
            date_obj = date
        
        new_date = date_obj + timedelta(days=int(days))
        return new_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError, AttributeError):
        return date
```

### 条件映射
商品状态到Schema.org条件的映射：
- `BRAND_NEW` → `https://schema.org/NewCondition`
- `OPEN_BOX` → `https://schema.org/RefurbishedCondition`
- `SCRATCH_DENT` → `https://schema.org/RefurbishedCondition`
- `USED_GOOD` → `https://schema.org/UsedCondition`
- `USED_FAIR` → `https://schema.org/UsedCondition`

### 保修类型映射
保修类型到Schema.org保修范围的映射：
- `MANUFACTURER` → `https://schema.org/ManufacturerWarranty`
- `STORE` → `https://schema.org/ExtendedWarranty`
- `THIRD_PARTY` → `https://schema.org/ExtendedWarranty`

## 验证方法

### 1. Google结构化数据测试工具
访问 [Google结构化数据测试工具](https://search.google.com/test/rich-results) 验证实现。

### 2. 验证步骤
1. 部署代码到测试环境
2. 访问任意商品详情页面
3. 复制页面URL到Google测试工具
4. 检查是否有错误或警告
5. 验证富媒体卡片预览

### 3. 预期结果
- 无结构化数据错误
- 显示产品信息卡片
- 显示面包屑导航
- 显示价格信息
- 显示店铺信息

## 扩展功能

### 评分和评论
预留了评分和评论的结构化数据实现：
```json
{
  "@type": "AggregateRating",
  "ratingValue": "4.5",
  "reviewCount": "128",
  "bestRating": "5",
  "worstRating": "1"
}
```

### 未来扩展
- 添加FAQ结构化数据
- 添加视频内容结构化数据
- 添加相关产品推荐
- 添加库存状态实时更新

## 注意事项

1. **数据完整性**: 确保所有必需字段都有值
2. **URL有效性**: 确保所有URL都是绝对路径
3. **图片可用性**: 确保图片URL可访问
4. **价格格式**: 价格必须是数字格式
5. **日期格式**: 日期必须符合ISO 8601格式

## 监控和维护

1. 定期使用Google Search Console监控结构化数据状态
2. 关注Google的算法更新和Schema.org规范变化
3. 根据用户反馈优化结构化数据内容
4. 监控富媒体卡片的点击率和转化率

## 文件修改清单

1. `frontend/templates/frontend/item_detail.html` - 添加结构化数据标记
2. `frontend/templatetags/frontend_filters.py` - 添加日期计算过滤器
3. `docs/structured_data_implementation.md` - 本文档

## 测试建议

1. 在不同商品类型上测试结构化数据
2. 验证有图片和无图片商品的显示
3. 测试不同保修类型的显示
4. 验证价格信息的准确性
5. 检查移动端和桌面端的显示效果
