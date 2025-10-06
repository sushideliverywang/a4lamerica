# SEO页面产品查询诊断脚本使用说明

## 脚本功能

`check_seo_page_products.py` 脚本用于诊断SEO页面的产品筛选条件，帮助您：
1. 检查筛选条件是否正确
2. 查看每一步筛选后的商品数量
3. 找出为什么某个SEO页面查不到商品

## 使用方法

### 1. 列出所有SEO页面

```bash
python scripts/check_seo_page_products.py --list
```

这会显示所有配置的SEO页面及其状态。

### 2. 检查特定SEO页面

```bash
python scripts/check_seo_page_products.py lg-truesteam-dishwasher-norcross
```

或者使用完整路径：

```bash
python /path/to/a4lamerica/scripts/check_seo_page_products.py lg-truesteam-dishwasher-norcross
```

### 3. 检查其他页面示例

```bash
# 检查Door in Door冰箱页面
python scripts/check_seo_page_products.py door-in-door-refrigerators-doraville

# 检查Bosch洗碗机页面
python scripts/check_seo_page_products.py bosch-800-series-dishwashers-duluth

# 检查All-in-One洗衣机页面
python scripts/check_seo_page_products.py all-in-one-washer-dryer-sandy-springs
```

## 输出说明

脚本会分步显示以下信息：

### 1. 页面基本信息
- 页面标题
- 城市
- 最少库存要求

### 2. 筛选条件详情
显示所有配置的筛选条件（basic、category、brand、product_model等）

### 3. 分步检查结果
- 总库存数量
- 已发布库存数量
- 已发布且未售出数量
- 符合公司条件的数量
- 符合类别条件的数量
- 符合品牌条件的数量
- 符合描述关键字的数量

### 4. 最终结果
- 符合所有条件的库存总数
- 前10个匹配产品的详细信息

## 诊断问题

### 如果查不到商品，脚本会帮您找出问题：

1. **类别不匹配**
   - 脚本会显示数据库中所有可用的类别
   - 检查配置的类别名称是否与数据库匹配

2. **品牌不匹配**
   - 脚本会显示数据库中所有可用的品牌
   - 检查品牌名称是否正确

3. **描述关键字不匹配**
   - 脚本会显示所有符合品牌和类别的产品描述
   - 用✓和✗标记哪些产品描述包含关键字
   - 可以看到是否需要调整关键字

4. **没有已发布的商品**
   - 检查是否所有符合条件的商品都未发布

5. **商品已售出**
   - 检查是否所有商品都已关联订单

## 示例输出

```
================================================================================
检查 SEO 页面: lg-truesteam-dishwasher-norcross
================================================================================

✓ 页面标题: Best LG TrueSteam Dishwashers in Norcross GA - Appliances 4 Less
✓ 简短标题: LG TrueSteam Dishwashers
✓ 城市: norcross
✓ 最少库存: 1

筛选条件:
--------------------------------------------------------------------------------

BASIC:
  - published: True
  - order__isnull: True
  - company_id: from_settings

CATEGORY:
  - names: ['Dishwasher']

BRAND:
  - name__iexact: LG

PRODUCT_MODEL:
  - description__icontains: truesteam

================================================================================

✓ 筛选器构建成功

生成的Django Q对象:
  (AND: ('published', True), ('order__isnull', True), ('company_id', 1),
   ('model_number__category__name__in', ['Dishwasher']),
   ('model_number__brand__name__iexact', 'LG'),
   ('model_number__description__icontains', 'truesteam'))

================================================================================
分步检查筛选条件
================================================================================

1. 总库存数量: 1250
2. 已发布库存: 450
3. 已发布且未售出: 320
4. 公司ID (从settings): 1
   符合公司条件: 320

5. 类别筛选: ['Dishwasher']
   数据库中所有类别: ['Refrigerator', 'Dishwasher', 'Washer', 'Dryer', ...]
   匹配的类别: ['Dishwasher']
   符合类别条件: 45
   示例产品型号:
     - LG LDT7808BD
     - Samsung DW80R9950US
     - Bosch SHPM88Z75N

6. 品牌筛选: {'name__iexact': 'LG'}
   数据库中所有品牌: ['LG', 'Samsung', 'Bosch', 'GE', ...]
   符合品牌条件: 12
   示例产品型号:
     - LG LDT7808BD
     - LG LDP6810SS
     - LG LDF5545ST

7. 产品模型筛选: {'description__icontains': 'truesteam'}
   描述关键字: 'truesteam'

   当前筛选下的产品型号数量: 12
   产品描述示例:
     ✓ LG LDT7808BD: LG QuadWash with TrueSteam technology...
     ✗ LG LDP6810SS: LG SteamClean dishwasher...
     ✓ LG LDF5545ST: Premium TrueSteam dishwasher with smart features...

   符合描述关键字条件: 5

   匹配的产品:
     - LG LDT7808BD
     - LG LDF5545ST

================================================================================
最终筛选结果
================================================================================

✓ 符合所有条件的库存数量: 5

找到的产品:

  控制号: CN12345
  品牌: LG
  型号: LDT7808BD
  类别: Dishwasher
  描述: LG QuadWash with TrueSteam technology...
  零售价: $899.00
  已发布: True
  订单: None
```

## 在服务器上运行

如果在服务器上运行，确保：

1. 激活虚拟环境（如果使用）
```bash
source venv/bin/activate
```

2. 从项目根目录运行
```bash
cd /path/to/a4lamerica
python scripts/check_seo_page_products.py lg-truesteam-dishwasher-norcross
```

## 常见问题

### Q: 脚本显示找到商品，但网站上看不到？
A: 可能原因：
- 检查nginx/apache配置是否正确
- 检查views.py中的查询逻辑是否与脚本一致
- 检查缓存是否需要清除

### Q: 如何修改筛选条件？
A: 编辑 `frontend/config/product_seo_pages.py` 文件，修改对应页面的filters配置

### Q: 如何添加新的筛选条件？
A: 在filters中添加新的筛选类型，然后更新 `build_product_filters` 函数

## 技术支持

如有问题，请检查：
1. Django设置是否正确
2. 数据库连接是否正常
3. COMPANY_ID是否在settings中配置
