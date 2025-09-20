# Home页面城市网格优化 - 2025年1月14日

## 修改概述
修改了home页面桌面端城市列表的显示，从一行四个改为一行五个城市卡片。

## 修改内容

### HTML容器调整 (`frontend/templates/frontend/home.html`)

#### 修改前
```html
<div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-text-primary mb-6 text-center">Free Delivery to Neighborhood</h2>
    <div class="city-grid">
```

#### 修改后
```html
<div class="max-w-6xl mx-auto">
    <h2 class="text-2xl font-bold text-text-primary mb-6 text-center">Free Delivery to Neighborhood</h2>
    <div class="city-grid">
```

### CSS样式调整 (`frontend/static/frontend/css/base_frontend.css`)

#### 修改前
```css
/* 桌面端样式 - 与category.html中的product-card完全一致 */
@media (min-width: 768px) {
    .city-card {
        flex: 0 0 160px;
        min-width: 160px;
        max-width: 160px;
        width: 160px;
        aspect-ratio: 1/1; /* 改为1:1正方形 */
        margin-bottom: 1.5rem;
    }
}
```

#### 修改后
```css
/* 桌面端样式 - 一行显示5个城市卡片 */
@media (min-width: 768px) {
    .city-card {
        flex: 0 0 calc(20% - 1.2rem);
        min-width: calc(20% - 1.2rem);
        max-width: calc(20% - 1.2rem);
        width: calc(20% - 1.2rem);
        aspect-ratio: 1/1; /* 1:1正方形 */
        margin-bottom: 1.5rem;
    }
}
```

## 技术细节

### 宽度计算
- **容器宽度**: 从max-w-4xl (896px) 改为 max-w-6xl (1152px)
- **卡片数量**: 5个
- **间距**: 1.5rem = 24px
- **总间距**: 4个间距 = 96px
- **可用宽度**: 1152px - 96px = 1056px
- **每个卡片宽度**: 1056px / 5 = 211.2px

### CSS实现
- 使用 `calc(20% - 1.2rem)` 实现响应式宽度
- 20% = 100% / 5（5个卡片）
- 1.2rem = 1.5rem * 4 / 5（平均分配间距）

### 响应式设计
- **移动端**: 保持2列网格布局不变
- **桌面端**: 从4列改为5列
- **保持**: 1:1正方形比例

## 视觉效果

### 布局变化
- **修改前**: 一行显示4个城市卡片
- **修改后**: 一行显示5个城市卡片
- **间距**: 保持1.5rem不变
- **比例**: 保持1:1正方形

### 用户体验
- 更多城市在首屏可见
- 减少滚动需求
- 保持视觉平衡
- 响应式适配

## 兼容性

### 浏览器支持
- 现代浏览器完全支持
- `calc()` 函数广泛支持
- `flex` 布局兼容性好

### 响应式断点
- 移动端：`max-width: 767px` - 2列网格
- 桌面端：`min-width: 768px` - 5列flex布局

## 业务价值

### 用户体验
- 更多城市选项可见
- 减少用户滚动操作
- 提高信息密度

### 视觉设计
- 保持设计一致性
- 优化空间利用
- 提升页面美观度

### 性能优化
- 减少页面高度
- 提高首屏内容密度
- 保持加载性能

## 测试建议
1. 在不同屏幕尺寸下测试显示效果
2. 验证城市卡片点击功能正常
3. 检查响应式断点切换
4. 确认间距和比例正确

## 后续优化
1. 根据实际使用情况调整卡片大小
2. 考虑添加hover效果
3. 优化移动端显示
4. 监控用户交互数据
