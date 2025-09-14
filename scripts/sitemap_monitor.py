#!/usr/bin/env python3
"""
Sitemap监控脚本
用于定期检查sitemap系统的性能和可用性
"""

import os
import sys
import django
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import json
from urllib.parse import urljoin

# 添加Django项目路径
sys.path.append('/var/www/a4lamerica')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a4lamerica.settings')
django.setup()

from django.conf import settings
from frontend.models_proxy import Location, Category, InventoryItem

class SitemapMonitor:
    def __init__(self, base_url=None):
        self.base_url = base_url or getattr(settings, 'SITE_URL', 'http://localhost:8000')
        self.logger = self.setup_logger()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'checks': {}
        }
    
    def setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('sitemap_monitor')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录 - 自动检测环境
        if os.path.exists('/var/www/a4lamerica'):
            # 生产环境
            log_dir = '/var/www/a4lamerica/logs'
        else:
            # 开发环境
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(f'{log_dir}/sitemap_monitor.log')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def check_sitemap_availability(self):
        """检查sitemap可用性 - 使用直接Django视图调用避免DNS解析延迟"""
        self.logger.info("开始检查sitemap可用性...")
        
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
            ('sitemap-warranty.xml', 'warranty'),
            ('sitemap-terms.xml', 'terms'),
        ]
        
        availability_results = {}
        factory = RequestFactory()
        
        for url_path, section in sitemap_sections:
            try:
                start_time = time.time()
                
                # 直接调用Django视图，避免HTTP请求和DNS解析
                request = factory.get(f'/{url_path}')
                # 使用正确的域名，避免ALLOWED_HOSTS错误
                host = self.base_url.replace('https://', '').replace('http://', '')
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
                    content_length = len(response.content) if hasattr(response, 'content') else 0
                    
                    availability_results[f'/{url_path}'] = {
                        'status': 'success',
                        'status_code': response.status_code,
                        'response_time': round(response_time, 3),
                        'content_length': content_length,
                        'method': 'direct_django_view'
                    }
                    self.logger.info(f"✓ {url_path} - 可用 ({response_time:.3f}s)")
                else:
                    availability_results[f'/{url_path}'] = {
                        'status': 'error',
                        'status_code': response.status_code,
                        'error': f'HTTP {response.status_code}',
                        'method': 'direct_django_view'
                    }
                    self.logger.error(f"✗ {url_path} - HTTP {response.status_code}")
                    
            except Exception as e:
                availability_results[f'/{url_path}'] = {
                    'status': 'error',
                    'error': str(e),
                    'method': 'direct_django_view'
                }
                self.logger.error(f"✗ {url_path} - 生成失败: {e}")
        
        self.results['checks']['availability'] = availability_results
        return availability_results
    
    def check_sitemap_content(self):
        """检查sitemap内容质量 - 使用直接Django视图调用避免DNS解析延迟"""
        self.logger.info("开始检查sitemap内容质量...")
        
        from django.test import RequestFactory
        from django.contrib.sitemaps.views import sitemap
        from frontend.views import sitemaps
        
        content_results = {}
        factory = RequestFactory()
        
        # 检查主sitemap
        try:
            request = factory.get('/sitemap.xml')
            request.META['HTTP_HOST'] = self.base_url.replace('https://', '').replace('http://', '')
            response = sitemap(request, sitemaps)
            
            if response.status_code == 200:
                # 确保response内容被渲染
                if hasattr(response, 'render'):
                    response.render()
                content_results['main_sitemap'] = self.analyze_sitemap_content(response.content.decode('utf-8'), 'sitemapindex')
            else:
                content_results['main_sitemap'] = {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            content_results['main_sitemap'] = {'error': str(e)}
        
        # 检查各个子sitemap
        sub_sitemaps = ['static', 'stores', 'categories', 'products', 'warranty', 'terms']
        for sitemap_type in sub_sitemaps:
            try:
                request = factory.get(f'/sitemap-{sitemap_type}.xml')
                # 使用正确的域名，避免ALLOWED_HOSTS错误
                host = self.base_url.replace('https://', '').replace('http://', '')
                request.META['HTTP_HOST'] = host
                request.META['SERVER_NAME'] = host.split(':')[0]  # 去掉端口号
                response = sitemap(request, {sitemap_type: sitemaps[sitemap_type]})
                
                if response.status_code == 200:
                    # 确保response内容被渲染
                    if hasattr(response, 'render'):
                        response.render()
                    content_results[f'sitemap_{sitemap_type}'] = self.analyze_sitemap_content(response.content.decode('utf-8'), 'urlset')
                else:
                    content_results[f'sitemap_{sitemap_type}'] = {'error': f'HTTP {response.status_code}'}
            except Exception as e:
                content_results[f'sitemap_{sitemap_type}'] = {'error': str(e)}
        
        self.results['checks']['content'] = content_results
        return content_results
    
    def analyze_sitemap_content(self, xml_content, expected_root):
        """分析sitemap内容"""
        try:
            root = ET.fromstring(xml_content)
            
            if root.tag == expected_root:
                if expected_root == 'urlset':
                    urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                    return {
                        'type': 'urlset',
                        'url_count': len(urls),
                        'has_valid_structure': True,
                        'sample_urls': [url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text 
                                      for url in urls[:3] if url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc') is not None]
                    }
                elif expected_root == 'sitemapindex':
                    sitemaps = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
                    return {
                        'type': 'sitemapindex',
                        'sitemap_count': len(sitemaps),
                        'has_valid_structure': True
                    }
            else:
                return {
                    'error': f'Unexpected root element: {root.tag}'
                }
        except ET.ParseError as e:
            return {
                'error': f'XML解析错误: {e}'
            }
        except Exception as e:
            return {
                'error': f'分析错误: {e}'
            }
    
    def check_database_content(self):
        """检查数据库内容统计"""
        self.logger.info("开始检查数据库内容统计...")
        
        try:
            company_id = getattr(settings, 'COMPANY_ID', 58)
            
            db_stats = {
                'locations': {
                    'total': Location.objects.count(),
                    'active': Location.objects.filter(is_active=True).count(),
                    'company_filtered': Location.objects.filter(company_id=company_id, is_active=True).count()
                },
                'categories': {
                    'total': Category.objects.count(),
                    'with_slug': Category.objects.filter(slug__isnull=False).exclude(slug='').count()
                },
                'products': {
                    'total': InventoryItem.objects.count(),
                    'published': InventoryItem.objects.filter(published=True).count(),
                    'company_filtered': InventoryItem.objects.filter(company_id=company_id, published=True).count()
                }
            }
            
            self.results['checks']['database'] = db_stats
            self.logger.info(f"数据库统计: {json.dumps(db_stats, indent=2)}")
            return db_stats
            
        except Exception as e:
            error_msg = f"数据库检查失败: {e}"
            self.logger.error(error_msg)
            self.results['checks']['database'] = {'error': error_msg}
            return {'error': error_msg}
    
    def check_performance(self):
        """检查性能指标 - 使用直接Django视图调用避免DNS解析延迟"""
        self.logger.info("开始检查性能指标...")
        
        from django.test import RequestFactory
        from django.contrib.sitemaps.views import sitemap
        from frontend.views import sitemaps
        import time
        
        performance_results = {}
        factory = RequestFactory()
        
        # 测试各个sitemap的响应时间
        sitemap_sections = [
            ('sitemap.xml', None),  # 主索引
            ('sitemap-static.xml', 'static'),
            ('sitemap-stores.xml', 'stores'),
            ('sitemap-categories.xml', 'categories'),
            ('sitemap-products.xml', 'products'),
        ]
        
        for url_path, section in sitemap_sections:
            try:
                start_time = time.time()
                
                # 直接调用Django视图，避免HTTP请求和DNS解析
                request = factory.get(f'/{url_path}')
                # 使用正确的域名，避免ALLOWED_HOSTS错误
                host = self.base_url.replace('https://', '').replace('http://', '')
                request.META['HTTP_HOST'] = host
                request.META['SERVER_NAME'] = host.split(':')[0]  # 去掉端口号
                
                if section:
                    response = sitemap(request, {section: sitemaps[section]})
                else:
                    response = sitemap(request, sitemaps)
                
                end_time = time.time()
                response_time = end_time - start_time
                # 确保response内容被渲染
                if hasattr(response, 'render'):
                    response.render()
                content_size = len(response.content) if hasattr(response, 'content') else 0
                
                performance_results[f'/{url_path}'] = {
                    'response_time': round(response_time, 3),
                    'content_size': content_size,
                    'status_code': response.status_code,
                    'performance_rating': self.rate_performance(response_time, content_size),
                    'method': 'direct_django_view'
                }
                
                self.logger.info(f"{url_path}: {response_time:.3f}s, {content_size} bytes")
                
            except Exception as e:
                performance_results[url_path] = {
                    'error': str(e),
                    'performance_rating': 'error'
                }
                self.logger.error(f"{url_path}: 性能测试失败 - {e}")
        
        self.results['checks']['performance'] = performance_results
        return performance_results
    
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
    
    def generate_report(self):
        """生成监控报告"""
        self.logger.info("生成监控报告...")
        
        # 计算总体健康度
        health_score = self.calculate_health_score()
        
        report = {
            'timestamp': self.results['timestamp'],
            'base_url': self.results['base_url'],
            'health_score': health_score,
            'summary': self.generate_summary(),
            'details': self.results['checks']
        }
        
        # 保存报告到文件 - 使用相同的日志目录检测逻辑
        if os.path.exists('/var/www/a4lamerica'):
            # 生产环境
            log_dir = '/var/www/a4lamerica/logs'
        else:
            # 开发环境
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        
        report_file = f'{log_dir}/sitemap_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"监控报告已保存到: {report_file}")
        return report
    
    def calculate_health_score(self):
        """计算健康度分数"""
        total_checks = 0
        passed_checks = 0
        
        # 检查可用性
        if 'availability' in self.results['checks']:
            for url, result in self.results['checks']['availability'].items():
                total_checks += 1
                if result['status'] == 'success':
                    passed_checks += 1
        
        # 检查内容质量
        if 'content' in self.results['checks']:
            for sitemap, result in self.results['checks']['content'].items():
                total_checks += 1
                if 'error' not in result and result.get('has_valid_structure', False):
                    passed_checks += 1
        
        if total_checks == 0:
            return 0
        
        return round((passed_checks / total_checks) * 100, 2)
    
    def generate_summary(self):
        """生成摘要信息"""
        summary = {
            'total_sitemaps': 0,
            'available_sitemaps': 0,
            'total_urls': 0,
            'performance_issues': 0,
            'content_issues': 0
        }
        
        # 统计sitemap数量
        if 'availability' in self.results['checks']:
            summary['total_sitemaps'] = len(self.results['checks']['availability'])
            summary['available_sitemaps'] = sum(1 for r in self.results['checks']['availability'].values() 
                                              if r['status'] == 'success')
        
        # 统计URL数量
        if 'content' in self.results['checks']:
            for result in self.results['checks']['content'].values():
                if 'url_count' in result:
                    summary['total_urls'] += result['url_count']
                if 'error' in result:
                    summary['content_issues'] += 1
        
        # 统计性能问题
        if 'performance' in self.results['checks']:
            for result in self.results['checks']['performance'].values():
                if result.get('performance_rating') in ['poor', 'error']:
                    summary['performance_issues'] += 1
        
        return summary
    
    def run_full_check(self):
        """运行完整检查"""
        self.logger.info("开始运行完整的sitemap监控检查...")
        
        # 执行各项检查
        self.check_sitemap_availability()
        self.check_sitemap_content()
        self.check_database_content()
        self.check_performance()
        
        # 生成报告
        report = self.generate_report()
        
        self.logger.info(f"监控检查完成，健康度: {report['health_score']}%")
        return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sitemap监控工具')
    parser.add_argument('--base-url', help='基础URL', default='http://localhost:8000')
    parser.add_argument('--check', choices=['availability', 'content', 'database', 'performance', 'all'], 
                       default='all', help='检查类型')
    
    args = parser.parse_args()
    
    monitor = SitemapMonitor(base_url=args.base_url)
    
    if args.check == 'all':
        report = monitor.run_full_check()
    elif args.check == 'availability':
        monitor.check_sitemap_availability()
    elif args.check == 'content':
        monitor.check_sitemap_content()
    elif args.check == 'database':
        monitor.check_database_content()
    elif args.check == 'performance':
        monitor.check_performance()
    
    print(f"\n监控完成！健康度: {monitor.results.get('health_score', 'N/A')}%")

if __name__ == '__main__':
    main()
