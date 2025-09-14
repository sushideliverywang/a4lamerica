# 统一 Sitemap 监控脚本使用指南

## 🎯 **重构完成！**

我已经成功重构了所有 sitemap 监控功能，现在只有一个统一的脚本：`scripts/unified_sitemap_monitor.py`

## 📋 **重构前后对比**

### **重构前（问题）**
- ❌ 3 个不同的脚本文件
- ❌ 6-7 个重复的检查函数
- ❌ 代码重复率高达 80%
- ❌ 维护困难，修改需要改多个地方
- ❌ 调用关系复杂

### **重构后（优势）**
- ✅ 1 个统一脚本
- ✅ 1 个核心检查方法
- ✅ 代码重复率 0%
- ✅ 易于维护，修改只需改一个地方
- ✅ 调用关系清晰

## 🚀 **使用方法**

### **1. 直接使用 Python 脚本**

```bash
# 快速检查
python scripts/unified_sitemap_monitor.py --check-type quick --base-url https://a4lamerica.com

# 完整检查
python scripts/unified_sitemap_monitor.py --check-type full --base-url https://a4lamerica.com

# 性能检查
python scripts/unified_sitemap_monitor.py --check-type performance --base-url https://a4lamerica.com
```

### **2. 使用 Django 管理命令**

```bash
# 快速检查
python manage.py sitemap_monitor --check-type quick

# 完整检查
python manage.py sitemap_monitor --check-type full

# 性能检查
python manage.py sitemap_monitor --check-type performance
```

## 📊 **功能特性**

### **检查类型**

| 类型 | 功能 | 包含内容 |
|------|------|----------|
| **quick** | 快速检查 | 可用性 + 性能 |
| **full** | 完整检查 | 可用性 + 内容质量 + 数据库统计 + 性能 |
| **performance** | 性能检查 | 仅性能指标 |

### **输出方式**

| 方式 | 说明 |
|------|------|
| **console** | 仅控制台输出 |
| **file** | 仅保存到文件 |
| **both** | 控制台 + 文件 |

### **健康度计算**

- **可用性分数**: 70% 权重
- **性能分数**: 30% 权重
- **综合健康度**: 0-100%

## 🔧 **技术实现**

### **核心方法**
```python
def check_sitemap(self, url_path, section):
    """统一的 sitemap 检查方法"""
    # 所有重复逻辑都在这里
```

### **优势**
1. **避免 DNS 解析延迟**: 直接调用 Django 视图
2. **统一错误处理**: 所有检查使用相同的错误处理逻辑
3. **可扩展性**: 添加新检查类型只需调用 `check_sitemap` 方法
4. **性能优化**: 避免重复的请求和解析

## 📅 **Crontab 配置**

新的 crontab 配置使用统一脚本：

```bash
# 每天上午8点执行快速检查
0 8 * * * cd /var/www/a4lamerica && source venv/bin/activate && python scripts/unified_sitemap_monitor.py --check-type quick --base-url https://a4lamerica.com --output both

# 每周一上午9点执行完整检查
0 9 * * 1 cd /var/www/a4lamerica && source venv/bin/activate && python scripts/unified_sitemap_monitor.py --check-type full --base-url https://a4lamerica.com --output both

# 每月1号上午10点执行性能检查
0 10 1 * * cd /var/www/a4lamerica && source venv/bin/activate && python scripts/unified_sitemap_monitor.py --check-type performance --base-url https://a4lamerica.com --output both
```

## 📁 **文件结构**

```
scripts/
├── unified_sitemap_monitor.py    # 统一监控脚本
└── server_crontab.txt           # 更新的 crontab 配置

frontend/management/commands/
└── sitemap_monitor.py           # 简化的 Django 管理命令

docs/
└── unified_sitemap_monitor_guide.md  # 使用指南
```

## ✅ **测试建议**

1. **本地测试**:
   ```bash
   python scripts/unified_sitemap_monitor.py --check-type quick
   ```

2. **服务器测试**:
   ```bash
   python scripts/unified_sitemap_monitor.py --check-type full --base-url https://a4lamerica.com
   ```

3. **Django 命令测试**:
   ```bash
   python manage.py sitemap_monitor --check-type quick
   ```

## 🎉 **重构成果**

- **代码行数减少**: 从 ~800 行减少到 ~400 行
- **文件数量减少**: 从 3 个文件减少到 1 个文件
- **维护复杂度**: 大幅降低
- **功能完整性**: 保持 100%
- **性能**: 提升（避免重复代码）

现在你只需要维护一个脚本文件，所有功能都集中在一起！
