# 营业时间功能修复记录

## 问题描述
在首页轮播图中，店铺的营业时间没有正确显示，显示为"Hours not available"。

## 问题原因
1. 在`frontend/models_proxy.py`中缺少`BusinessHours`模型定义
2. 在`HomeView`和`StoreView`中没有预加载营业时间数据

## 解决方案

### 1. 添加BusinessHours模型
在`frontend/models_proxy.py`中添加了`BusinessHours`模型：

```python
class BusinessHours(models.Model):
    """营业时间模型代理"""
    DAYS_OF_WEEK = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='business_hours')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    is_24_hours = models.BooleanField(default=False)
    
    class Meta:
        managed = False
        db_table = 'organization_businesshours'
        ordering = ['day_of_week']
```

### 2. 添加模型方法
- `is_open_now` 属性：检查当前时间是否在营业时间内
- `get_today_hours()` 方法：获取今日营业时间的显示文本

### 3. 修复查询优化
在`HomeView`中更新了stores查询：
```python
stores = Location.objects.filter(
    location_type='STORE',
    is_active=True
).select_related('company', 'address').prefetch_related('business_hours').only(
    'name', 'address__street_number', 'address__street_name', 'address__city', 
    'address__state', 'address__zip_code', 'address__latitude', 'address__longitude',
    'image', 'company__company_name', 'timezone'
)
```

在`StoreView`中也添加了营业时间预加载：
```python
location = get_object_or_404(
    Location.objects.select_related('address', 'company').prefetch_related('business_hours'),
    slug=location_slug, 
    is_active=True
)
```

### 4. 修复Company模型
移除了Company模型中不存在的slug字段，避免数据库查询错误。

## 测试结果
通过测试脚本验证，营业时间功能现在正常工作：
- 成功获取店铺的营业时间数据
- 正确显示每日营业时间
- 正确判断当前是否营业
- 时区处理正确

## 修改文件
1. `frontend/models_proxy.py` - 添加BusinessHours模型，修复Company模型
2. `frontend/views.py` - 更新HomeView和StoreView的查询优化

## 日期
2024年12月19日
