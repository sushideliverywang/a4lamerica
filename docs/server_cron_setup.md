# 服务器Cron任务配置指南

## 1. 部署到服务器后的Cron配置

### 1.1 基本步骤

1. **将项目文件复制到服务器**
```bash
# 在服务器上创建目录
sudo mkdir -p /var/www/a4lamerica
sudo chown -R www-data:www-data /var/www/a4lamerica

# 复制项目文件（从你的开发机器）
scp -r . user@your-server:/var/www/a4lamerica/
```

2. **设置权限**
```bash
# 在服务器上设置权限
sudo chmod +x /var/www/a4lamerica/scripts/server_monitor.sh
sudo chmod -R 755 /var/www/a4lamerica
sudo chmod -R 777 /var/www/a4lamerica/logs
```

3. **设置虚拟环境**
```bash
cd /var/www/a4lamerica
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.2 配置Cron任务

#### 方法1：使用提供的配置文件
```bash
# 编辑crontab
crontab -e

# 复制并粘贴以下内容（已更新为正确路径）：
```

```bash
# 每天上午8点执行快速检查（生产环境）
0 8 * * * /var/www/a4lamerica/scripts/server_monitor.sh

# 每周一上午9点执行完整检查
0 9 * * 1 cd /var/www/a4lamerica && source venv/bin/activate && python manage.py monitor_sitemap --check-type full --base-url https://a4lamerica.com --output both

# 每月1号上午10点执行深度检查
0 10 1 * * cd /var/www/a4lamerica && source venv/bin/activate && python scripts/sitemap_monitor.py --base-url https://a4lamerica.com --check all

# 每天下午6点清理旧日志文件（保留30天）
0 18 * * * find /var/www/a4lamerica/logs -name "sitemap_*" -mtime +30 -delete
```

#### 方法2：手动添加单个任务
```bash
# 只添加每日快速检查
echo "0 8 * * * /var/www/a4lamerica/scripts/server_monitor.sh" | crontab -

# 或者添加完整检查
echo "0 9 * * 1 cd /var/www/a4lamerica && source venv/bin/activate && python manage.py monitor_sitemap --check-type full --base-url https://a4lamerica.com --output both" | crontab -
```

## 2. Cron任务说明

### 2.1 任务频率说明

| 任务 | 频率 | 时间 | 说明 |
|------|------|------|------|
| **快速检查** | 每天 | 上午8点 | 检查sitemap可用性，发送邮件通知 |
| **完整检查** | 每周一 | 上午9点 | 详细检查sitemap内容和性能 |
| **深度检查** | 每月1号 | 上午10点 | 全面分析sitemap系统状态 |
| **日志清理** | 每天 | 下午6点 | 删除30天前的旧日志文件 |

### 2.2 任务输出

- **快速检查**: 输出到 `/var/www/a4lamerica/logs/cron.log`
- **完整检查**: 输出到控制台和日志文件
- **深度检查**: 生成详细报告到 `/var/www/a4lamerica/logs/`

## 3. 测试Cron配置

### 3.1 测试脚本权限
```bash
# 测试监控脚本是否可以执行
/var/www/a4lamerica/scripts/server_monitor.sh

# 检查输出
tail -f /var/www/a4lamerica/logs/cron.log
```

### 3.2 测试Django命令
```bash
cd /var/www/a4lamerica
source venv/bin/activate

# 测试快速检查
python manage.py monitor_sitemap --check-type quick --base-url https://a4lamerica.com --output both

# 测试完整检查
python manage.py monitor_sitemap --check-type full --base-url https://a4lamerica.com --output both
```

### 3.3 测试独立脚本
```bash
cd /var/www/a4lamerica
source venv/bin/activate

# 测试sitemap监控脚本
python scripts/sitemap_monitor.py --base-url https://a4lamerica.com --check all
```

## 4. 监控和故障排除

### 4.1 查看Cron日志
```bash
# 查看系统cron日志
sudo tail -f /var/log/cron

# 查看项目cron日志
tail -f /var/www/a4lamerica/logs/cron.log

# 查看sitemap监控日志
tail -f /var/www/a4lamerica/logs/sitemap_monitor.log
```

### 4.2 检查Cron任务状态
```bash
# 查看当前用户的cron任务
crontab -l

# 查看cron服务状态
sudo systemctl status cron

# 重启cron服务
sudo systemctl restart cron
```

### 4.3 常见问题解决

#### 问题1：脚本没有执行权限
```bash
# 解决方案
sudo chmod +x /var/www/a4lamerica/scripts/server_monitor.sh
```

#### 问题2：Python路径问题
```bash
# 解决方案：在脚本中使用绝对路径
#!/bin/bash
export PATH="/var/www/a4lamerica/venv/bin:$PATH"
```

#### 问题3：Django环境变量问题
```bash
# 解决方案：在cron任务中设置环境变量
0 8 * * * cd /var/www/a4lamerica && export DJANGO_SETTINGS_MODULE=a4lamerica.settings && /var/www/a4lamerica/scripts/server_monitor.sh
```

## 5. 邮件通知配置

### 5.1 配置邮件服务
在 `/var/www/a4lamerica/.env` 文件中添加：
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5.2 测试邮件发送
```bash
cd /var/www/a4lamerica
source venv/bin/activate
python manage.py shell

# 在Django shell中测试邮件
from django.core.mail import send_mail
send_mail('测试邮件', '这是一封测试邮件', 'from@example.com', ['to@example.com'])
```

## 6. 性能优化建议

### 6.1 调整检查频率
根据你的网站更新频率调整cron任务：

- **高更新频率**：每天检查
- **中等更新频率**：每2-3天检查
- **低更新频率**：每周检查

### 6.2 日志轮转
创建日志轮转配置 `/etc/logrotate.d/a4lamerica`：
```
/var/www/a4lamerica/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### 6.3 监控磁盘空间
```bash
# 添加磁盘空间检查到cron
0 7 * * * df -h /var/www/a4lamerica | awk 'NR==2{print $5}' | sed 's/%//' | awk '{if($1>80) print "警告: 磁盘空间使用率超过80%"}' | mail -s "磁盘空间警告" admin@a4lamerica.com
```

## 7. 安全建议

### 7.1 文件权限
```bash
# 设置安全的文件权限
sudo chmod 600 /var/www/a4lamerica/.env
sudo chmod 644 /var/www/a4lamerica/scripts/server_crontab.txt
sudo chmod 755 /var/www/a4lamerica/scripts/server_monitor.sh
```

### 7.2 日志安全
```bash
# 确保日志文件只有www-data用户可以写入
sudo chown -R www-data:www-data /var/www/a4lamerica/logs
sudo chmod -R 640 /var/www/a4lamerica/logs
```

## 8. 备份策略

### 8.1 自动备份脚本
创建 `/var/www/a4lamerica/scripts/backup.sh`：
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/www/a4lamerica/backups"
mkdir -p $BACKUP_DIR

# 备份项目文件
tar -czf $BACKUP_DIR/project_backup_$DATE.tar.gz -C /var/www/a4lamerica .

# 备份数据库（如果需要）
# pg_dump your_database > $BACKUP_DIR/db_backup_$DATE.sql

# 保留最近7天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 8.2 添加备份到Cron
```bash
# 每天凌晨3点执行备份
0 3 * * * /var/www/a4lamerica/scripts/backup.sh
```

现在你的 `server_crontab.txt` 文件已经完全更新为正确的服务器路径，可以直接用于生产环境配置了！
