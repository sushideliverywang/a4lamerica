"""
Sitemap监控管理命令
提供简化的sitemap监控功能
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
from datetime import datetime
import os


class Command(BaseCommand):
    help = '监控sitemap系统性能和可用性。使用直接Django视图调用避免DNS解析延迟，提供更准确的性能数据'

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
            default='console',
            help='输出方式'
        )

    def handle(self, *args, **options):
        base_url = options['base_url']
        check_type = options['check_type']
        output = options['output']
        
        self.stdout.write(
            self.style.SUCCESS(f'开始sitemap监控检查 - {check_type}模式')
        )
        
        if check_type == 'quick':
            results = self.quick_check(base_url)
        elif check_type == 'full':
            results = self.full_check(base_url)
        elif check_type == 'performance':
            results = self.performance_check(base_url)
        
        # 输出结果
        if output in ['console', 'both']:
            self.display_results(results)
        
        if output in ['file', 'both']:
            self.save_results(results)
        
        self.stdout.write(
            self.style.SUCCESS('监控检查完成！')
        )

    def quick_check(self, base_url):
        """快速检查 - 直接调用Django视图，避免DNS解析延迟"""
        self.stdout.write('执行快速检查...')
        
        from django.test import RequestFactory
        from django.contrib.sitemaps.views import sitemap
        from frontend.views import sitemaps
        import time
        
        sitemap_sections = [
            ('sitemap.xml', None),  # 主索引
            ('sitemap-static.xml', 'static'),
            ('sitemap-stores.xml', 'stores'),
            ('sitemap-categories.xml', 'categories'),
            ('sitemap-products.xml', 'products'),
        ]
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'check_type': 'quick',
            'base_url': base_url,
            'sitemaps': {}
        }
        
        factory = RequestFactory()
        
        for url_path, section in sitemap_sections:
            try:
                start_time = time.time()
                
                # 直接调用Django视图，避免HTTP请求和DNS解析
                request = factory.get(f'/{url_path}')
                # 使用正确的域名，避免ALLOWED_HOSTS错误
                host = base_url.replace('https://', '').replace('http://', '')
                request.META['HTTP_HOST'] = host
                request.META['SERVER_NAME'] = host.split(':')[0]  # 去掉端口号
                
                if section:
                    response = sitemap(request, {section: sitemaps[section]})
                else:
                    response = sitemap(request, sitemaps)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # 确保response内容被渲染
                    if hasattr(response, 'render'):
                        response.render()
                    content_size = len(response.content) if hasattr(response, 'content') else 0
                    
                    results['sitemaps'][f'/{url_path}'] = {
                        'status': 'OK',
                        'response_time': round(response_time, 3),
                        'size': content_size,
                        'method': 'direct_django_view'
                    }
                else:
                    results['sitemaps'][f'/{url_path}'] = {
                        'status': 'ERROR',
                        'error': f'HTTP {response.status_code}',
                        'method': 'direct_django_view'
                    }
                    
            except Exception as e:
                results['sitemaps'][f'/{url_path}'] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'method': 'direct_django_view'
                }
        
        return results

    def full_check(self, base_url):
        """完整检查 - 包括内容和性能"""
        self.stdout.write('执行完整检查...')
        
        results = self.quick_check(base_url)
        results['check_type'] = 'full'
        
        # 添加内容分析
        results['content_analysis'] = self.analyze_content(base_url)
        
        # 添加性能分析
        results['performance_analysis'] = self.analyze_performance(base_url)
        
        return results

    def performance_check(self, base_url):
        """性能检查 - 专注于性能指标"""
        self.stdout.write('执行性能检查...')
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'check_type': 'performance',
            'base_url': base_url,
            'performance_metrics': {}
        }
        
        sitemap_urls = [
            '/sitemap.xml',
            '/sitemap-static.xml',
            '/sitemap-stores.xml',
            '/sitemap-categories.xml',
            '/sitemap-products.xml',
        ]
        
        for url_path in sitemap_urls:
            full_url = f"{base_url}{url_path}"
            try:
                start_time = datetime.now()
                response = requests.get(full_url, timeout=30)
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds()
                content_size = len(response.content)
                
                results['performance_metrics'][url_path] = {
                    'response_time': response_time,
                    'content_size': content_size,
                    'status_code': response.status_code,
                    'rating': self.rate_performance(response_time, content_size)
                }
                
            except Exception as e:
                results['performance_metrics'][url_path] = {
                    'error': str(e),
                    'rating': 'error'
                }
        
        return results

    def analyze_content(self, base_url):
        """分析sitemap内容"""
        content_analysis = {}
        
        # 分析主sitemap
        try:
            response = requests.get(f"{base_url}/sitemap.xml", timeout=30)
            if response.status_code == 200:
                content_analysis['main_sitemap'] = self.count_urls_in_xml(response.text)
        except Exception as e:
            content_analysis['main_sitemap'] = {'error': str(e)}
        
        return content_analysis

    def count_urls_in_xml(self, xml_content):
        """计算XML中的URL数量"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            return {'url_count': len(urls)}
        except Exception as e:
            return {'error': str(e)}

    def analyze_performance(self, base_url):
        """分析性能指标"""
        performance_analysis = {
            'total_response_time': 0,
            'average_response_time': 0,
            'slowest_sitemap': None,
            'fastest_sitemap': None
        }
        
        sitemap_urls = [
            '/sitemap.xml',
            '/sitemap-static.xml',
            '/sitemap-stores.xml',
            '/sitemap-categories.xml',
            '/sitemap-products.xml',
        ]
        
        response_times = []
        
        for url_path in sitemap_urls:
            full_url = f"{base_url}{url_path}"
            try:
                response = requests.get(full_url, timeout=30)
                if response.status_code == 200:
                    response_time = response.elapsed.total_seconds()
                    response_times.append((url_path, response_time))
            except Exception:
                pass
        
        if response_times:
            performance_analysis['total_response_time'] = sum(rt for _, rt in response_times)
            performance_analysis['average_response_time'] = performance_analysis['total_response_time'] / len(response_times)
            performance_analysis['slowest_sitemap'] = max(response_times, key=lambda x: x[1])
            performance_analysis['fastest_sitemap'] = min(response_times, key=lambda x: x[1])
        
        return performance_analysis

    def rate_performance(self, response_time, content_size):
        """评估性能等级"""
        if response_time < 1.0:
            return 'excellent'
        elif response_time < 3.0:
            return 'good'
        elif response_time < 5.0:
            return 'fair'
        else:
            return 'poor'

    def display_results(self, results):
        """在控制台显示结果"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Sitemap监控报告 - {results["check_type"].upper()}')
        self.stdout.write('='*50)
        
        if 'sitemaps' in results:
            self.stdout.write('\nSitemap可用性:')
            for url, data in results['sitemaps'].items():
                if data['status'] == 'OK':
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {url} - {data["response_time"]:.2f}s - {data["size"]} bytes')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {url} - {data["error"]}')
                    )
        
        if 'performance_metrics' in results:
            self.stdout.write('\n性能指标:')
            for url, data in results['performance_metrics'].items():
                if 'error' not in data:
                    rating_color = {
                        'excellent': self.style.SUCCESS,
                        'good': self.style.SUCCESS,
                        'fair': self.style.WARNING,
                        'poor': self.style.ERROR
                    }.get(data['rating'], self.style.WARNING)
                    
                    self.stdout.write(
                        rating_color(f'{url}: {data["response_time"]:.2f}s ({data["rating"]})')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'{url}: {data["error"]}')
                    )
        
        if 'content_analysis' in results:
            self.stdout.write('\n内容分析:')
            for sitemap, data in results['content_analysis'].items():
                if 'url_count' in data:
                    self.stdout.write(f'{sitemap}: {data["url_count"]} URLs')
                else:
                    self.stdout.write(f'{sitemap}: {data["error"]}')

    def save_results(self, results):
        """保存结果到文件"""
        # 创建日志目录 - 自动检测环境
        if os.path.exists('/var/www/a4lamerica'):
            # 生产环境
            log_dir = '/var/www/a4lamerica/logs'
        else:
            # 开发环境 - 使用Django的BASE_DIR
            from django.conf import settings
            log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 保存JSON报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{log_dir}/sitemap_monitor_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'\n结果已保存到: {filename}')
