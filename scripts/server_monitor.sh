#!/bin/bash
# 服务器端sitemap监控脚本
# 用于生产环境监控

# 设置环境变量
export DJANGO_SETTINGS_MODULE=a4lamerica.settings
export PYTHONPATH=/var/www/a4lamerica

# 切换到项目目录
cd /var/www/a4lamerica

# 激活虚拟环境（根据实际虚拟环境路径修改）
source venv/bin/activate

# 生产环境监控命令
echo "开始监控生产环境sitemap..."
python manage.py monitor_sitemap --check-type quick --base-url https://a4lamerica.com --output both

# 如果健康度低于80%，发送邮件通知
HEALTH_SCORE=$(python -c "
import json
import glob
import os
reports = glob.glob('logs/sitemap_report_*.json')
if reports:
    latest = max(reports, key=os.path.getctime)
    with open(latest) as f:
        data = json.load(f)
    print(data.get('health_score', 0))
else:
    print(0)
")

if [ "$HEALTH_SCORE" -lt 80 ]; then
    echo "警告: Sitemap健康度低于80% ($HEALTH_SCORE%)" | mail -s "Sitemap监控警告 - 生产环境" james@a4lamerica.com
fi

echo "生产环境监控完成 - $(date)"
