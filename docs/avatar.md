# Avatar 功能实现方案

## 1. 功能概述
作为accounts app的一部分，头像（avatar）功能集成到用户注册流程中，作为可选步骤。用户可以在完成注册信息时上传并裁剪头像，也可以使用默认头像。

## 实现进度
### 已完成 ✓
1. 数据库设计和实现
   - 添加了avatar字段到Subscriber模型
   - 实现了文件命名和管理方法
   - 添加了get_avatar_url方法
   - 在complete_registration.html中显示临时头像
   - 最终注册时将临时头像移动到avatars目录

2. 基础设施配置
   - 配置了媒体文件存储（MEDIA_URL和MEDIA_ROOT）
   - 设置了文件访问URL
   - 移除了photo_crop app

3. 静态文件配置
   - 创建了crop.css和crop.js
   - 创建了crop_avatar.html模板
   - 配置了静态文件目录结构

4. 文件系统准备
   - 创建了media/avatars目录
   - 创建了media/temp/uploads目录
   - 添加了默认头像文件

5. 头像裁剪功能
   - [x] 实现圆形裁剪界面
   - [x] 支持图片拖拽和缩放
   - [x] 保存临时文件到temp/uploads目录

6. 自动清理机制
   - [x] 配置每日凌晨1点（美东时间）执行清理任务
   - [x] 实现过期注册数据清理
   - [x] 实现临时头像文件清理
   - [x] 添加完整的日志记录

## 2. 数据库设计
```python
class Subscriber(models.Model):
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Avatar',
        help_text='User profile picture (2x2 inch)'
    )

    def get_avatar_url(self):
        """返回用户头像URL，如果没有则返回默认头像"""
        if self.avatar:
            return self.avatar.url
        return f"{settings.MEDIA_URL}avatars/default.png"

    def generate_avatar_filename(self):
        """根据用户邮箱生成唯一的头像文件名"""
        email_hash = hashlib.md5(self.email.encode()).hexdigest()
        return f"avatars/{email_hash}.png"

    def save(self, *args, **kwargs):
        if self.avatar:
            new_name = self.generate_avatar_filename()
            if self.avatar.name != new_name:
                if os.path.isfile(self.avatar.path):
                    os.remove(self.avatar.path)
                self.avatar.name = new_name
        super().save(*args, **kwargs)
```

### 已实现的功能
1. 数据库字段：
   - 添加了avatar字段，支持空值
   - 添加了字段说明和帮助文本

2. 头像URL处理：
   - 实现了get_avatar_url方法
   - 自动处理默认头像的情况

3. 文件管理：
   - 基于邮箱的唯一文件名生成
   - 自动清理旧头像文件
   - 文件重命名处理

## 3. 文件存储结构
```
media/
├── avatars/           # 用户头像目录
│   ├── default.png   # 默认头像
│   ├── [hash1].png   # 用户头像
│   └── [hash2].png
└── temp/             # 临时文件目录
    └── uploads/      # 上传的原始图片
```

### 头像文件命名规则
✓ 使用用户邮箱生成唯一哈希值：`hashlib.md5(email.encode()).hexdigest() + '.png'`
- 优点：
  - 同一用户更新头像时自动覆盖旧文件
  - 避免文件名冲突
  - 保护用户隐私（文件名不包含用户信息）
- 实现方式：
  - 通过Subscriber.generate_avatar_filename方法生成
  - 在save方法中自动处理文件重命名

## 4. 用户界面流程
1. complete_registration.html：
   - 显示头像上传按钮
   - 显示当前头像预览（默认或已上传）
   - 点击上传按钮跳转到裁剪页面

2. crop.html：
   - 显示2inch圆形裁剪框
   - 支持图片拖拽和缩放
   - 保存/取消按钮

3. 返回complete_registration.html：
   - 显示裁剪后的新头像
   - 继续完成注册流程

## 5. 技术实现
### URL 路由
```python
# accounts/urls.py
urlpatterns = [
    # 现有的URL保持不变...
    path('avatar/upload/', views.upload_avatar, name='upload_avatar'),
    path('avatar/crop/<str:token>/', views.crop_avatar, name='crop_avatar'),
    path('avatar/save/<str:token>/', views.save_avatar, name='save_avatar'),
]
```

### 视图功能
1. upload_avatar：
   - 处理文件上传
   - 验证文件类型和大小
   - 保存到临时目录
   - 重定向到裁剪页面

2. crop_avatar：
   - 显示圆形裁剪界面
   - 处理图片缩放和移动
   - 使用registration token验证用户

3. save_avatar：
   - 根据裁剪参数处理图片
   - 生成最终头像文件
   - 清理临时文件
   - 返回头像URL
   - 更新用户的avatar字段

## 6. 安全措施
1. 文件验证：
   - 限制文件类型（仅图片）
   - 限制文件大小（最大2MB）
   - 验证文件内容

2. 访问控制：
   - 使用现有的registration token进行验证
   - 验证临时文件关联
   - 防止未授权访问

3. 文件管理：
   - 定期清理临时文件
   - 自动覆盖旧头像

## 7. 文件组织
```
accounts/
├── templates/accounts/
│   ├── complete_registration.html
│   ├── crop_avatar.html      # 新增
│   └── ...
├── static/accounts/
│   ├── css/
│   │   └── crop.css         # 从photo_crop移动
│   ├── js/
│   │   └── crop.js          # 从photo_crop移动
│   └── ...
├── views/
│   ├── registration.py      # 现有注册相关视图
│   ├── avatar.py           # 新增头像相关视图
│   └── ...
└── ...
```

## 8. 兼容性处理
1. 数据库兼容：
   - avatar字段可为空
   - 现有用户显示默认头像

2. 界面兼容：
   - 所有显示头像的地方判断是否存在
   - 不存在时显示默认头像

## 9. 性能优化
1. 图片处理：
   - 统一输出为合适尺寸的PNG
   - 压缩文件大小
   - 优化加载速度

2. 存储优化：
   - 单一目录存储便于管理
   - 哈希文件名便于缓存

## 10. 后续规划
1. 个人设置中修改头像
2. 支持头像缓存和CDN
3. 支持更多图片格式
4. 添加头像审核功能

## 11. 紧急问题修复
3. 功能问题
   - [ ] 处理文件权限问题
     - [ ] 部署时的权限设置
       - [ ] 创建media目录结构
       - [ ] 设置Apache用户为所有者
       - [ ] 设置正确的目录权限（755）
       - [ ] 设置正确的文件权限（644）
       - [ ] Apache配置
         - [ ] 添加media目录访问权限
         - [ ] 验证静态文件服务是否正确

## 12. 后续开发
1. 头像上传功能
   - [ ] 添加图片压缩功能
     - [ ] 限制最大尺寸（例如500x500）
     - [ ] 压缩文件大小但保持质量
   - [ ] 支持更多图片格式（jpg, webp等）

2. 头像裁剪功能
   - [ ] 优化裁剪体验
     - [ ] 添加缩放指示器
     - [ ] 优化移动端操作
     - [ ] 添加裁剪预览

3. 文件处理
   - [ ] 完善文件管理
     - [ ] 监控临时文件清理效果
     - [ ] 添加文件备份机制
     - [ ] 优化存储空间使用

4. 集成测试
   - [ ] 测试注册流程中的头像上传
   - [ ] 验证默认头像显示
   - [ ] 检查错误处理
