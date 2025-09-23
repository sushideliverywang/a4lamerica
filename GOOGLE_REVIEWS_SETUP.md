# Google Reviews 集成设置指南

## 🔧 配置步骤

### 1. 获取Google Places API密钥

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Places API**
4. 创建API密钥并设置限制（推荐限制为Places API）

### 2. 获取Google Place ID

使用以下方法之一获取你的商店的Place ID：

**方法1: 使用Google Place ID Finder**
1. 访问 [Place ID Finder](https://developers.google.com/maps/documentation/places/web-service/place-id)
2. 搜索你的商店名称和地址
3. 复制返回的Place ID

**方法2: 使用API查询**
```bash
curl "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=Appliances%204%20Less%20Doraville&inputtype=textquery&fields=place_id,name,formatted_address&key=YOUR_API_KEY"
```

### 3. 配置环境变量

在你的 `.env` 文件中添加：

```env
# Google Places API配置
GOOGLE_PLACES_API_KEY=your_api_key_here
GOOGLE_PLACE_ID=your_place_id_here
```

### 4. 在Django settings中配置

在 `settings.py` 中添加：

```python
# Google Places API 配置
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
GOOGLE_PLACE_ID = os.getenv('GOOGLE_PLACE_ID')
```

## 🎨 前端模板集成

模板已经准备好显示Google评论。评论将显示在首页的"What Our Customers Say"部分。

### 评论展示特点：
- 响应式网格布局（手机1列，平板2列，桌面3列）
- 星级评分显示
- 客户头像（如果有）
- 评论时间
- 链接到Google Maps查看所有评论

## 🔄 缓存和性能

- 评论数据缓存1小时，避免频繁API调用
- 开发模式下如果API失败会显示示例数据
- 支持最多6条评论显示

## 📊 监控和维护

### 定期检查事项：
1. **API配额使用** - 确保不超过Google Places API限制
2. **评论内容** - 定期查看新评论，及时回复
3. **评分变化** - 监控平均评分趋势

### 管理命令测试

创建管理命令来测试API连接：

```python
# frontend/management/commands/test_google_reviews.py
from django.core.management.base import BaseCommand
from frontend.services.google_reviews import test_google_reviews_api

class Command(BaseCommand):
    help = 'Test Google Reviews API connection'

    def handle(self, *args, **options):
        test_google_reviews_api()
```

运行测试：
```bash
python manage.py test_google_reviews
```

## 🛠️ 故障排除

### 常见问题：

1. **API密钥无效**
   - 检查密钥是否正确复制
   - 确认Places API已启用
   - 检查API密钥限制设置

2. **Place ID错误**
   - 验证Place ID格式正确
   - 确认对应的是正确的商店位置

3. **评论不显示**
   - 检查Django缓存是否正常
   - 查看日志文件中的错误信息
   - 确认模板变量传递正确

4. **API配额超限**
   - 检查Google Cloud Console中的API使用情况
   - 考虑增加缓存时间
   - 优化API调用频率

## 📈 SEO优势

集成Google评论后的SEO益处：

1. **社会证明** - 真实客户反馈提升信任度
2. **内容更新** - 定期新增的评论内容
3. **本地SEO** - 强化Google My Business连接
4. **用户生成内容** - 搜索引擎喜爱的真实内容
5. **评分显示** - 可能在搜索结果中显示星级

## 🔐 安全注意事项

1. **API密钥保护** - 永远不要在前端代码中暴露API密钥
2. **环境变量** - 使用环境变量存储敏感信息
3. **API限制** - 设置API密钥使用限制和域名限制
4. **错误处理** - 优雅处理API失败情况

## 🚀 上线检查清单

- [ ] API密钥和Place ID配置正确
- [ ] 生产环境环境变量设置
- [ ] API配额和计费设置检查
- [ ] 评论显示测试（桌面和移动端）
- [ ] 缓存功能验证
- [ ] 错误日志监控设置
- [ ] Google My Business信息完善