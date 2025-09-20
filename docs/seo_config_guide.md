# SEO配置系统使用指南

## 概述

`frontend/config/seo_keywords.py` 是一个硬编码的"数据库"文件，用于管理城市和服务的静态配置信息。这个文件类似于数据库，但所有数据都是硬编码的，便于快速修改和部署。

## 文件结构

### 服务类型配置 (SERVICE_TYPES)

每个服务包含以下字段：

```python
'service_key': {
    'name': '服务显示名称',
    'keywords': ['关键词1', '关键词2', '关键词3'],
    'description': '服务详细描述',
    'price_range': '价格范围',
    'duration': '预计服务时长',
    'features': ['特点1', '特点2', '特点3'],
    'image_desktop': '桌面版图片路径',
    'image_mobile': '移动版图片路径',
    'icon': '图标名称',
    'category': '服务分类'
}
```

### 城市配置 (CITIES)

每个城市包含以下字段：

```python
'city_key': {
    'name': '城市名称',
    'state': '州名',
    'full_name': '完整城市名',
    'nearby_cities': ['附近城市1', '附近城市2'],
    'description': '城市介绍',
    'population': '人口数量',
    'area': '面积',
    'image_desktop': '桌面版图片路径',
    'image_mobile': '移动版图片路径',
    'highlights': ['特色1', '特色2', '特色3']
}
```

## 如何添加新服务

1. 在 `SERVICE_TYPES` 中添加新的服务配置
2. 确保包含所有必需字段
3. 添加对应的图片文件到 `static/frontend/images/services/` 目录
4. 重启服务器

示例：
```python
'new_service': {
    'name': 'New Service',
    'keywords': ['new', 'service', 'keyword'],
    'description': 'Description of the new service',
    'price_range': '$50-$100',
    'duration': '1 hour',
    'features': ['Feature 1', 'Feature 2'],
    'image_desktop': '/static/frontend/images/services/Desktop-new-service.jpg',
    'image_mobile': '/static/frontend/images/services/Mobile-new-service.jpg',
    'icon': 'new-icon',
    'category': 'new-category'
}
```

## 如何添加新城市

1. 在 `CITIES` 中添加新的城市配置
2. 确保包含所有必需字段
3. 添加对应的图片文件到 `static/frontend/images/city/` 目录
4. 更新相关城市的 `nearby_cities` 列表
5. 重启服务器

示例：
```python
'new_city': {
    'name': 'New City',
    'state': 'GA',
    'full_name': 'New City, GA',
    'nearby_cities': ['City1', 'City2', 'City3'],
    'description': 'Description of the new city',
    'population': '50,000+',
    'area': '10.0 sq mi',
    'image_desktop': '/static/frontend/images/city/Desktop-New-City.jpg',
    'image_mobile': '/static/frontend/images/city/Mobile-New-City.jpg',
    'highlights': ['Highlight 1', 'Highlight 2']
}
```

## 图片文件命名规范

### 服务图片
- 桌面版：`Desktop-{service-name}.jpg`
- 移动版：`Mobile-{service-name}.jpg`
- 位置：`static/frontend/images/services/`

### 城市图片
- 桌面版：`Desktop-{city-name}.jpg`
- 移动版：`Mobile-{city-name}.jpg`
- 位置：`static/frontend/images/city/`

## 在模板中使用

### 服务信息
```html
{{ service_info.name }}          <!-- 服务名称 -->
{{ service_info.description }}   <!-- 服务描述 -->
{{ service_info.price_range }}   <!-- 价格范围 -->
{{ service_info.duration }}      <!-- 服务时长 -->
{{ service_info.features }}      <!-- 服务特点列表 -->
{{ service_info.image_desktop }} <!-- 桌面版图片 -->
{{ service_info.image_mobile }}  <!-- 移动版图片 -->
```

### 城市信息
```html
{{ city_info.name }}             <!-- 城市名称 -->
{{ city_info.description }}      <!-- 城市描述 -->
{{ city_info.population }}       <!-- 人口数量 -->
{{ city_info.area }}             <!-- 面积 -->
{{ city_info.highlights }}       <!-- 城市特色列表 -->
{{ city_info.image_desktop }}    <!-- 桌面版图片 -->
{{ city_info.image_mobile }}     <!-- 移动版图片 -->
```

## 注意事项

1. **键名一致性**：确保 `city_key` 和 `service_key` 在URL中使用时保持一致
2. **图片路径**：确保图片文件存在且路径正确
3. **字段完整性**：添加新服务或城市时，确保包含所有必需字段
4. **重启服务器**：修改配置后需要重启Django服务器才能生效
5. **备份**：修改前建议备份原配置文件

## 优势

- **快速部署**：无需数据库迁移，直接修改文件即可
- **版本控制**：配置变更可以通过Git跟踪
- **简单维护**：非技术人员也可以轻松修改内容
- **性能优化**：静态配置加载速度快
- **灵活性**：可以随时添加新字段而不影响现有功能
