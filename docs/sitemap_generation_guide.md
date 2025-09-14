# 网站地图生成指南

## 问题解决

之前 `generate_sitemap.py` 命令在生产环境中仍然使用 `localhost:8000` 作为基础URL，现在已经修复。

## 修改内容

1. **自动环境检测**: 命令现在会自动从 `settings.SITE_URL` 获取正确的域名
2. **环境信息显示**: 命令会显示当前运行环境（开发/生产）和使用的域名
3. **灵活配置**: 仍然支持手动指定 `--base-url` 参数

## 使用方法

### 生产环境（推荐）
```bash
# 自动使用 settings.SITE_URL (https://a4lamerica.com)
python manage.py generate_sitemap

# 带验证
python manage.py generate_sitemap --validate
```

### 开发环境
```bash
# 自动使用 settings.SITE_URL (http://192.168.1.83:8000)
python manage.py generate_sitemap

# 手动指定URL
python manage.py generate_sitemap --base-url http://localhost:8000
```

## 输出示例

```
开始生成网站地图... (生产环境, 使用域名: https://a4lamerica.com)
✓ https://a4lamerica.com/sitemap.xml - 成功生成
✓ https://a4lamerica.com/sitemap-static.xml - 成功生成
✓ https://a4lamerica.com/sitemap-stores.xml - 成功生成
✓ https://a4lamerica.com/sitemap-categories.xml - 成功生成
✓ https://a4lamerica.com/sitemap-products.xml - 成功生成
✓ https://a4lamerica.com/sitemap-warranty.xml - 成功生成
✓ https://a4lamerica.com/sitemap-terms.xml - 成功生成

网站地图生成完成！
```

## 配置说明

- **开发环境**: 使用 `http://192.168.1.83:8000` (来自 settings.py)
- **生产环境**: 使用 `https://a4lamerica.com` (来自 settings.py)
- **手动覆盖**: 使用 `--base-url` 参数指定任意URL

## 注意事项

1. 确保在生产环境中 `settings.SITE_URL` 已正确配置
2. 如果遇到网络问题，可以先用 `--base-url` 指定内网地址测试
3. 建议定期运行此命令更新网站地图
