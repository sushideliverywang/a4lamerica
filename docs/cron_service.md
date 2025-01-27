# Cron Service Configuration Guide (macOS)

本文档描述了如何在macOS环境下配置和管理Django的定时任务服务。该服务主要用于清理过期的注册数据和临时文件。

## 1. 初始设置

### 1.1 安装依赖
```bash
pip install django-crontab
```

### 1.2 创建日志文件（重要）
在部署时必须手动创建日志文件并设置正确的权限：
# 注意：macOS系统下Apache用户是_www
```bash
# 创建日志目录和文件
sudo mkdir -p /var/log/apache2
sudo touch /var/log/apache2/cron.log
sudo touch /var/log/apache2/a4lamerica_error.log

# 设置权限
sudo chmod 755 /var/log/apache2
sudo chmod 644 /var/log/apache2/cron.log
sudo chmod 644 /var/log/apache2/a4lamerica_error.log

# 设置所有者为Apache用户（macOS使用_www）
sudo chown _www:_www /var/log/apache2/cron.log
sudo chown _www:_www /var/log/apache2/a4lamerica_error.log

# 添加当前用户到Apache组（macOS使用dseditgroup命令）
sudo dseditgroup -o edit -a $USER -t user _www
```

### 1.3 Django配置
在`settings.py`中添加应用：
```python
INSTALLED_APPS = [
    ...
    'django_crontab',
]
```

### 1.4 Cron任务配置
在`settings.py`中添加以下配置：
```python
CRONJOBS = [
    ('0 1 * * *', 'accounts.tasks.cleanup_expired_registrations', 
     '>> /var/log/apache2/cron.log 2>&1')  # 每天凌晨1点执行
]

CRONTAB_LOCK_JOBS = True
CRONTAB_COMMAND_PREFIX = 'DJANGO_SETTINGS_MODULE=a4lamerica.settings'
```

## 2. 系统配置

### 2.1 检查cron服务
```bash
# 检查服务状态
sudo launchctl list | grep cron

# 如果服务未运行，启动服务
sudo launchctl load -w /System/Library/LaunchDaemons/com.vix.cron.plist
```

### 2.2 日志配置
```bash
# 创建日志目录和文件
sudo mkdir -p /var/log/apache2
sudo touch /var/log/apache2/cron.log

# 设置权限
sudo chmod 755 /var/log/apache2
sudo chmod 644 /var/log/apache2/cron.log
```

## 3. 任务管理

### 3.1 基本操作
```bash
# 添加cron任务
python manage.py crontab add

# 查看当前任务
python manage.py crontab show

# 移除任务
python manage.py crontab remove
```
### 3.2 监控和调试
```bash
# 实时查看日志
tail -f /var/log/apache2/cron.log

# 手动测试任务
python manage.py shell
>>> from accounts.tasks import cleanup_expired_registrations
>>> cleanup_expired_registrations()
```

## 4. 维护指南

### 4.1 服务器重启后检查清单
1. 检查cron服务状态
2. 确认服务是否需要重启：
```bash
sudo launchctl load -w /System/Library/LaunchDaemons/com.vix.cron.plist
```
3. 验证任务是否存在：
```bash
python manage.py crontab show
python manage.py crontab add  # 如果需要
```

### 4.2 故障排查
1. 检查服务状态：
```bash
sudo launchctl list | grep cron
```
2. 检查日志文件权限：
```bash
ls -l /var/log/apache2/cron.log
```
3. 确认crontab配置：
```bash
crontab -l
```

### 4.3 日常维护建议
1. 定期检查日志文件大小
2. 监控任务执行情况
3. 确保日志目录有足够空间
4. 定期验证数据清理是否正常进行

## 5. 补充说明

### 5.1 清理任务说明
该服务自动清理：
- 过期的注册token
- 未完成注册的用户数据
- 临时上传的头像文件

### 5.2 相关文件
- `a4lamerica/settings.py`: cron配置
- `accounts/tasks.py`: 清理任务实现
- `/var/log/apache2/cron.log`: 任务日志

### 5.3 注意事项
1. 任务默认每天凌晨1点执行
2. 修改任务配置后需要重新添加cron任务
3. 确保系统时间正确设置

