# Sitemap监控和维护指南

## 📊 **监控系统概述**

为了确保sitemap系统持续稳定运行，我们提供了多层次的监控方案：

1. **实时监控** - 通过Django管理命令
2. **定期监控** - 通过cron任务自动执行
3. **性能监控** - 详细的性能指标分析
4. **内容监控** - 检查sitemap内容质量

## 🔧 **监控工具**

### 1. Django管理命令

**快速检查（推荐日常使用）:**
```bash
# 检查sitemap可用性
python manage.py monitor_sitemap --check-type quick

# 检查生产环境
python manage.py monitor_sitemap --base-url https://a4lamerica.com --check-type quick
```

**完整检查（推荐每周使用）:**
```bash
# 完整检查包括内容和性能
python manage.py monitor_sitemap --check-type full --output both
```

**性能检查（推荐每月使用）:**
```bash
# 专注于性能指标
python manage.py monitor_sitemap --check-type performance --output file
```

### 2. 独立监控脚本

**运行完整监控:**
```bash
# 使用独立脚本
python scripts/sitemap_monitor.py --base-url https://a4lamerica.com --check all
```

**检查特定项目:**
```bash
# 只检查可用性
python scripts/sitemap_monitor.py --check availability

# 只检查内容质量
python scripts/sitemap_monitor.py --check content

# 只检查性能
python scripts/sitemap_monitor.py --check performance
```

## ⏰ **定期监控计划**

### 1. 日常监控（每天）

**时间:** 每天早上8点
**命令:**
```bash
python manage.py monitor_sitemap --check-type quick --base-url https://a4lamerica.com
```

**检查项目:**
- 所有sitemap文件是否可访问
- 响应时间是否正常（< 3秒）
- HTTP状态码是否正常（200）

### 2. 周度监控（每周）

**时间:** 每周一早上9点
**命令:**
```bash
python manage.py monitor_sitemap --check-type full --base-url https://a4lamerica.com --output both
```

**检查项目:**
- 所有日常检查项目
- sitemap内容质量分析
- URL数量统计
- 性能指标分析

### 3. 月度监控（每月）

**时间:** 每月1号早上10点
**命令:**
```bash
python scripts/sitemap_monitor.py --base-url https://a4lamerica.com --check all
```

**检查项目:**
- 所有周度检查项目
- 数据库内容统计
- 健康度评分
- 详细性能报告

## 📈 **性能指标标准**

### 1. 响应时间标准

| 等级 | 响应时间 | 说明 |
|------|----------|------|
| 优秀 | < 1秒 | 性能极佳 |
| 良好 | 1-3秒 | 性能良好 |
| 一般 | 3-5秒 | 性能可接受 |
| 较差 | > 5秒 | 需要优化 |

### 2. 健康度评分

- **90-100%**: 优秀，系统运行完美
- **80-89%**: 良好，系统运行正常
- **70-79%**: 一般，需要关注
- **< 70%**: 较差，需要立即处理

### 3. 内容质量标准

- **URL数量**: 应该与数据库内容匹配
- **XML格式**: 必须符合sitemap标准
- **链接有效性**: 所有URL必须可访问
- **更新频率**: 内容应该是最新的

## 🚨 **告警机制**

### 1. 自动告警条件

**严重告警（立即处理）:**
- 任何sitemap返回非200状态码
- 响应时间超过10秒
- 健康度低于70%

**警告（24小时内处理）:**
- 响应时间超过5秒
- 健康度低于80%
- 内容数量异常

**提醒（1周内处理）:**
- 响应时间超过3秒
- 健康度低于90%
- 性能评级为"一般"

### 2. 告警通知

**邮件通知:**
```bash
# 在cron脚本中配置
if [ "$HEALTH_SCORE" -lt 80 ]; then
    echo "警告: Sitemap健康度低于80% ($HEALTH_SCORE%)" | mail -s "Sitemap监控警告" admin@a4lamerica.com
fi
```

**日志记录:**
- 所有监控结果保存在 `logs/sitemap_monitor.log`
- 详细报告保存在 `logs/sitemap_report_*.json`

## 📋 **监控检查清单**

### 每日检查清单

- [ ] 主sitemap索引可访问
- [ ] 所有子sitemap可访问
- [ ] 响应时间正常
- [ ] 无HTTP错误
- [ ] 检查监控日志

### 每周检查清单

- [ ] 执行完整监控
- [ ] 检查内容质量
- [ ] 分析性能趋势
- [ ] 验证URL数量
- [ ] 检查错误日志

### 每月检查清单

- [ ] 执行深度监控
- [ ] 分析健康度趋势
- [ ] 检查数据库内容
- [ ] 优化性能问题
- [ ] 更新监控配置

## 🔍 **故障排除**

### 1. 常见问题

**Sitemap不可访问:**
```bash
# 检查Django服务状态
python manage.py runserver --check

# 检查URL配置
python manage.py show_urls | grep sitemap

# 检查视图函数
python manage.py shell -c "from frontend.views import sitemap_view; print('OK')"
```

**响应时间过慢:**
```bash
# 检查数据库查询
python manage.py shell -c "
from frontend.sitemaps import ProductSitemap
ps = ProductSitemap()
items = list(ps.items())
print(f'Products: {len(items)}')
"

# 检查服务器资源
top -p $(pgrep -f "python manage.py runserver")
```

**内容数量异常:**
```bash
# 检查数据库内容
python manage.py shell -c "
from frontend.models_proxy import InventoryItem, Category, Location
print(f'Products: {InventoryItem.objects.filter(published=True).count()}')
print(f'Categories: {Category.objects.filter(slug__isnull=False).count()}')
print(f'Locations: {Location.objects.filter(is_active=True).count()}')
"
```

### 2. 性能优化

**数据库优化:**
```python
# 在sitemaps.py中添加索引提示
def items(self):
    return InventoryItem.objects.filter(
        company_id=company_id,
        published=True
    ).select_related('model_number', 'location').only(
        'id', 'updated_at', 'model_number', 'location'
    ).order_by('-created_at')
```

**缓存优化:**
```python
# 在settings.py中添加缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
```

## 📊 **监控报告示例**

### 快速检查报告
```
Sitemap监控报告 - QUICK
==================================================

Sitemap可用性:
✓ /sitemap.xml - 0.45s - 1234 bytes
✓ /sitemap-static.xml - 0.23s - 567 bytes
✓ /sitemap-stores.xml - 0.34s - 234 bytes
✓ /sitemap-categories.xml - 0.67s - 3456 bytes
✓ /sitemap-products.xml - 1.23s - 12345 bytes
```

### 性能检查报告
```
性能指标:
/sitemap.xml: 0.45s (excellent)
/sitemap-static.xml: 0.23s (excellent)
/sitemap-stores.xml: 0.34s (excellent)
/sitemap-categories.xml: 0.67s (excellent)
/sitemap-products.xml: 1.23s (good)
```

## 🎯 **最佳实践**

### 1. 监控频率

- **生产环境**: 每天检查
- **开发环境**: 每周检查
- **测试环境**: 按需检查

### 2. 告警设置

- **响应时间**: 超过5秒告警
- **错误率**: 超过5%告警
- **健康度**: 低于80%告警

### 3. 报告保存

- **日志文件**: 保留30天
- **报告文件**: 保留90天
- **错误日志**: 永久保留

### 4. 团队协作

- **开发团队**: 负责性能优化
- **运维团队**: 负责监控配置
- **SEO团队**: 负责内容质量

## 📞 **联系支持**

如果遇到监控问题，请联系：

- **技术负责人**: 开发团队
- **运维负责人**: 运维团队
- **紧急联系**: 24/7支持热线

---

**注意**: 定期监控是确保sitemap系统稳定运行的关键。建议按照本指南建立监控流程，并定期检查和优化系统性能。
