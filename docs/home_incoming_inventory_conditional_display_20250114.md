# 首页即将到货区域条件显示功能实现

## 修改日期
2025年1月14日

## 功能描述
在首页的即将到货区域添加条件显示逻辑：
- 当有即将到货的库存时，显示原有的"Preview Incoming Inventory"按钮
- 当没有即将到货的库存时，显示注册账号的提示和按钮

## 实现细节

### 后端修改 (frontend/views.py)

1. **在 `HomeView` 中添加库存检查方法**：
   ```python
   def _check_incoming_inventory(self):
       """
       检查是否有即将到货的库存
       使用与IncomingInventoryView相同的逻辑
       """
       # 使用与IncomingInventoryView相同的过滤逻辑
       tracking_states = [1, 2, 3]  # 追踪的状态ID

       # 获取状态为CONVERTING的LoadManifest，使用配置中的公司ID
       load_manifests = LoadManifest.objects.filter(
           status=LoadManifest.Status.CONVERTING,
           company_id=settings.COMPANY_ID
       )

       # 检查是否有任何批次包含即将到货的商品
       for manifest in load_manifests:
           inventory_items = InventoryItem.objects.filter(
               load_number=manifest,
               current_state_id__in=tracking_states
           )
           if inventory_items.exists():
               return True
       
       return False
   ```

2. **在 `get_context_data` 中添加库存检查**：
   ```python
   # 检查是否有即将到货的库存
   has_incoming_inventory = self._check_incoming_inventory()

   context.update({
       # ... 其他上下文数据
       'has_incoming_inventory': has_incoming_inventory,
   })
   ```

### 前端修改 (frontend/templates/frontend/home.html)

在即将到货区域添加条件判断：

1. **有库存时显示**：
   - 保持原有的卡车图片
   - 标题："Interested in upcoming arrivals?"
   - 描述："Browse upcoming arrivals that will be available for purchase soon!"
   - 按钮："Preview Incoming Inventory"（链接到 incoming_inventory 页面）

2. **无库存时显示**：
   - 显示通知图标
   - 标题："Stay Updated on New Arrivals"
   - 描述："Currently there are no upcoming arrivals. Register an account to receive notifications when new inventory becomes available!"
   - 按钮：
     - 如果用户已登录：链接到客户资料页面
     - 如果用户未登录：链接到注册页面

## 判断逻辑

使用与 `IncomingInventoryView` 相同的判断逻辑：
- 查找状态为 `CONVERTING` 的 `LoadManifest` 对象
- 检查这些批次中是否有状态为 1, 2, 3 的库存商品
- 如果有任何一个批次包含即将到货的商品，返回 `True`

## 技术要点

1. **性能优化**：使用简单的存在性检查，而不是加载完整数据
2. **代码复用**：与 `IncomingInventoryView` 使用相同的判断逻辑
3. **用户体验**：根据库存状态提供不同的用户引导
4. **响应式设计**：保持原有的响应式布局和样式

## 测试建议

1. 测试有即将到货库存时的显示效果
2. 测试无即将到货库存时的显示效果
3. 测试已登录和未登录用户的不同按钮行为
4. 验证链接的正确性
