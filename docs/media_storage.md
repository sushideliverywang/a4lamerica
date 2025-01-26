# 媒体文件存储配置指南

## 1. 将媒体文件迁移到外部SSD

### 1.1 基础配置
1. 修改Django设置（settings.py）：
```python
if not DEBUG:
    # 媒体文件配置
    MEDIA_URL = '/media/'
    MEDIA_ROOT = '/mnt/ssd/a4lamerica/media'  # 修改为SSD的挂载路径
```

2. 修改Apache配置：
```apache
# 添加新目录的访问权限
<Directory /mnt/ssd/a4lamerica/media>
    Require all granted
</Directory>

# 添加别名映射
Alias /media/ /mnt/ssd/a4lamerica/media/
```

### 1.2 目录设置
```bash
# 创建必要的目录结构
sudo mkdir -p /Volumes/SSD/a4lamerica/media/avatars
sudo mkdir -p /Volumes/SSD/a4lamerica/media/temp/uploads

# 设置目录所有者为Apache用户
sudo chown -R _www:_www /Volumes/SSD/a4lamerica/media

# 设置适当的权限
sudo chmod 755 /Volumes/SSD/a4lamerica/media
sudo chmod -R 755 /Volumes/SSD/a4lamerica/media/avatars
sudo chmod -R 755 /Volumes/SSD/a4lamerica/media/temp
```

### 1.3 配置SSD自动挂载
1. 获取SSD的UUID：
```bash
diskutil info /Volumes/SSD | grep UUID
```

2. 编辑/etc/fstab文件：
```bash
sudo vifs
```

3. 添加挂载配置：
```
UUID=your-ssd-uuid  /Volumes/SSD  apfs  rw,auto  0  2
```

### 1.4 数据迁移
1. 迁移现有文件：
```bash
# 备份现有文件
sudo cp -R /Library/WebServer/Documents/a4lamerica/media/* /Volumes/SSD/a4lamerica/media/

# 验证文件完整性
sudo diff -r /Library/WebServer/Documents/a4lamerica/media /Volumes/SSD/a4lamerica/media
```

2. 测试新配置：
```bash
# 重启Apache
sudo apachectl restart

# 检查日志是否有错误
sudo tail -f /var/log/apache2/error_log
```

## 2. 注意事项

### 2.1 权限检查
- 确保Apache用户(www-data)对新目录有读写权限
- 定期检查日志文件中的权限相关错误
- 确保目录权限设置正确（755目录，644文件）

### 2.2 性能考虑
- 使用SSD可以提高文件读写速度
- 考虑定期备份媒体文件
- 监控磁盘空间使用情况

### 2.3 故障排除
1. 文件权限问题：
```bash
# 重置权限
sudo find /Volumes/SSD/a4lamerica/media -type d -exec chmod 755 {} \;
sudo find /Volumes/SSD/a4lamerica/media -type f -exec chmod 644 {} \;
```

2. 挂载问题：
```bash
# 检查挂载状态
df -h
mount | grep SSD

# 手动挂载
diskutil mount SSD
```

3. Apache访问问题：
```bash
# 检查Apache配置
sudo apachectl -t

# 检查Apache日志
sudo tail -f /var/log/apache2/error_log
```

## 3. 备份策略
1. 定期备份：
```bash
# 创建每日备份脚本
#!/bin/bash
backup_date=$(date +%Y%m%d)
sudo rsync -av /Volumes/SSD/a4lamerica/media/ /backup/media_$backup_date/
```

2. 自动清理旧备份：
```bash
# 保留最近30天的备份
find /backup/ -name "media_*" -type d -mtime +30 -exec rm -rf {} \; 