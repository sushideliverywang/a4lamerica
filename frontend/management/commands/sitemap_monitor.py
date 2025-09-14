"""
简化的 Sitemap 监控管理命令
调用统一的监控脚本
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = '简化的 sitemap 监控命令，调用统一监控脚本'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            type=str,
            default=getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            help='网站基础URL'
        )
        parser.add_argument(
            '--check-type',
            choices=['quick', 'full', 'performance'],
            default='quick',
            help='检查类型: quick(快速), full(完整), performance(性能)'
        )
        parser.add_argument(
            '--output',
            choices=['console', 'file', 'both'],
            default='both',
            help='输出方式'
        )

    def handle(self, *args, **options):
        base_url = options['base_url']
        check_type = options['check_type']
        output = options['output']
        
        self.stdout.write(
            self.style.SUCCESS(f'开始 sitemap 监控检查 - {check_type} 模式')
        )
        
        # 获取脚本路径
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'scripts', 'unified_sitemap_monitor.py')
        script_path = os.path.abspath(script_path)
        
        # 构建命令
        cmd = [
            sys.executable,
            script_path,
            '--base-url', base_url,
            '--check-type', check_type,
            '--output', output
        ]
        
        try:
            # 执行统一监控脚本
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # 输出结果
            if result.stdout:
                self.stdout.write(result.stdout)
            if result.stderr:
                self.stdout.write(self.style.ERROR(result.stderr))
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS('监控检查完成！')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'监控检查失败，退出码: {result.returncode}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'执行监控脚本时出错: {e}')
            )
