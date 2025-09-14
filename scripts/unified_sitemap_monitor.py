#!/usr/bin/env python3
"""
统一 Sitemap 监控脚本
整合所有 sitemap 监控功能，避免代码重复
"""

import os
import sys
import django
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# 添加Django项目路径 - 自动检测环境
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a4lamerica.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sitemaps.views import sitemap
from frontend.views import sitemaps
from frontend.models_proxy import Location, Category, InventoryItem
from django.conf import settings


class UnifiedSitemapMonitor:
    """统一的 Sitemap 监控类"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or getattr(settings, 'SITE_URL', 'http://localhost:8000')
        self.factory = RequestFactory()
        self.logger = self.setup_logger()
        
        # 统一的 sitemap 配置
        self.sitemap_sections = [
            ('sitemap.xml', None),  # 主索引
            ('sitemap-static.xml', 'static'),
            ('sitemap-stores.xml', 'stores'),
            ('sitemap-categories.xml', 'categories'),
            ('sitemap-products.xml', 'products'),
            ('sitemap-warranty.xml', 'warranty'),
            ('sitemap-terms.xml', 'terms'),
        ]
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'checks': {}
        }
    
    def setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('unified_sitemap_monitor')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录 - 自动检测环境
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        log_dir = os.path.join(project_root, 'logs')
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
    
    def check_sitemap(self, url_path, section):
        """统一的 sitemap 检查方法"""
        try:
            start_time = time.time()
            
            # 创建请求
            request = self.factory.get(f'/{url_path}')
            host = self.base_url.replace('https://', '').replace('http://', '')
            request.META['HTTP_HOST'] = host
            request.META['SERVER_NAME'] = host.split(':')[0]
            
            # 在开发环境中，使用 localhost 避免 ALLOWED_HOSTS 问题
            if '192.168.1.' in host or 'localhost' in host:
                request.META['HTTP_HOST'] = 'localhost:8000'
                request.META['SERVER_NAME'] = 'localhost'
            
            # 调用 sitemap 视图
            if section:
                response = sitemap(request, {section: sitemaps[section]})
            else:
                response = sitemap(request, sitemaps)
            
            response_time = time.time() - start_time
            
            # 确保 response 内容被渲染
            if hasattr(response, 'render'):
                response.render()
            
            content_size = len(response.content) if hasattr(response, 'content') else 0
            
            return {
                'status': 'success' if response.status_code == 200 else 'error',
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'content_size': content_size,
                'method': 'direct_django_view'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'method': 'direct_django_view'
            }
    
    def check_availability(self):
        """检查 sitemap 可用性"""
        self.logger.info("开始检查 sitemap 可用性...")
        
        availability_results = {}
        
        for url_path, section in self.sitemap_sections:
            result = self.check_sitemap(url_path, section)
            availability_results[f'/{url_path}'] = result
            
            if result['status'] == 'success':
                self.logger.info(f"✓ {url_path} - 可用 ({result['response_time']}s)")
            else:
                self.logger.error(f"✗ {url_path} - 失败: {result.get('error', 'Unknown error')}")
        
        self.results['checks']['availability'] = availability_results
        return availability_results
    
    def check_content_quality(self):
        """检查 sitemap 内容质量"""
        self.logger.info("开始检查 sitemap 内容质量...")
        
        content_results = {}
        
        for url_path, section in self.sitemap_sections:
            result = self.check_sitemap(url_path, section)
            
            if result['status'] == 'success':
                # 分析 XML 内容
                try:
                    import xml.etree.ElementTree as ET
                    xml_content = result.get('xml_content', '')
                    if not xml_content and hasattr(result, 'content'):
                        xml_content = result['content'].decode('utf-8')
                    
                    root = ET.fromstring(xml_content)
                    
                    if root.tag == 'urlset':
                        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                        content_results[f'/{url_path}'] = {
                            'url_count': len(urls),
                            'status': 'success',
                            'content_size': result['content_size']
                        }
                    elif root.tag == 'sitemapindex':
                        sitemaps = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
                        content_results[f'/{url_path}'] = {
                            'sitemap_count': len(sitemaps),
                            'status': 'success',
                            'content_size': result['content_size']
                        }
                except Exception as e:
                    content_results[f'/{url_path}'] = {
                        'status': 'error',
                        'error': f'XML解析失败: {e}',
                        'content_size': result['content_size']
                    }
            else:
                content_results[f'/{url_path}'] = result
        
        self.results['checks']['content'] = content_results
        return content_results
    
    def check_database_stats(self):
        """检查数据库统计"""
        self.logger.info("开始检查数据库统计...")
        
        try:
            company_id = getattr(settings, 'COMPANY_ID', None)
            
            # 商店统计
            locations = Location.objects.filter(company_id=company_id) if company_id else Location.objects.all()
            active_locations = locations.filter(is_active=True)
            
            # 分类统计
            categories = Category.objects.all()
            categories_with_slug = categories.exclude(slug__isnull=True).exclude(slug='')
            
            # 产品统计
            products = InventoryItem.objects.filter(company_id=company_id) if company_id else InventoryItem.objects.all()
            published_products = products.filter(published=True)
            
            stats = {
                'locations': {
                    'total': locations.count(),
                    'active': active_locations.count(),
                    'company_filtered': locations.count() if company_id else 'N/A'
                },
                'categories': {
                    'total': categories.count(),
                    'with_slug': categories_with_slug.count()
                },
                'products': {
                    'total': products.count(),
                    'published': published_products.count(),
                    'company_filtered': products.count() if company_id else 'N/A'
                }
            }
            
            self.logger.info(f"数据库统计: {json.dumps(stats, indent=2)}")
            self.results['checks']['database'] = stats
            return stats
            
        except Exception as e:
            error_msg = f"数据库检查失败: {e}"
            self.logger.error(error_msg)
            self.results['checks']['database'] = {'error': error_msg}
            return {'error': error_msg}
    
    def check_performance(self):
        """检查性能指标"""
        self.logger.info("开始检查性能指标...")
        
        performance_results = {}
        
        for url_path, section in self.sitemap_sections:
            result = self.check_sitemap(url_path, section)
            performance_results[f'/{url_path}'] = result
            
            if result['status'] == 'success':
                # 性能评级
                response_time = result['response_time']
                content_size = result['content_size']
                
                if response_time < 0.1:
                    rating = 'excellent'
                elif response_time < 0.5:
                    rating = 'good'
                elif response_time < 2.0:
                    rating = 'fair'
                else:
                    rating = 'poor'
                
                result['performance_rating'] = rating
                self.logger.info(f"{url_path}: {response_time}s, {content_size} bytes ({rating})")
            else:
                result['performance_rating'] = 'error'
                self.logger.error(f"{url_path}: 性能测试失败 - {result.get('error', 'Unknown error')}")
        
        self.results['checks']['performance'] = performance_results
        return performance_results
    
    def calculate_health_score(self):
        """计算健康度分数"""
        availability = self.results['checks'].get('availability', {})
        performance = self.results['checks'].get('performance', {})
        
        total_checks = len(availability)
        if total_checks == 0:
            return 0
        
        success_count = sum(1 for result in availability.values() if result.get('status') == 'success')
        availability_score = (success_count / total_checks) * 100
        
        # 性能分数（基于响应时间）
        performance_scores = []
        for result in performance.values():
            if result.get('status') == 'success':
                response_time = result.get('response_time', 0)
                if response_time < 0.1:
                    performance_scores.append(100)
                elif response_time < 0.5:
                    performance_scores.append(80)
                elif response_time < 2.0:
                    performance_scores.append(60)
                else:
                    performance_scores.append(40)
        
        performance_score = sum(performance_scores) / len(performance_scores) if performance_scores else 0
        
        # 综合健康度（可用性70% + 性能30%）
        health_score = (availability_score * 0.7) + (performance_score * 0.3)
        return round(health_score, 1)
    
    def generate_report(self):
        """生成监控报告"""
        health_score = self.calculate_health_score()
        
        report = {
            'timestamp': self.results['timestamp'],
            'base_url': self.base_url,
            'health_score': health_score,
            'checks': self.results['checks']
        }
        
        # 保存报告到文件 - 自动检测环境
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        log_dir = Path(os.path.join(project_root, 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = log_dir / f'sitemap_report_{timestamp_str}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"监控报告已保存到: {report_file}")
        return report
    
    def run_quick_check(self):
        """运行快速检查"""
        self.logger.info("开始快速检查...")
        self.check_availability()
        self.check_performance()
        return self.generate_report()
    
    def run_full_check(self):
        """运行完整检查"""
        self.logger.info("开始完整检查...")
        self.check_availability()
        self.check_content_quality()
        self.check_database_stats()
        self.check_performance()
        return self.generate_report()
    
    def run_performance_check(self):
        """运行性能检查"""
        self.logger.info("开始性能检查...")
        self.check_performance()
        return self.generate_report()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一 Sitemap 监控工具')
    parser.add_argument('--base-url', help='基础URL', default=None)
    parser.add_argument('--check-type', choices=['quick', 'full', 'performance'], 
                       default='quick', help='检查类型')
    parser.add_argument('--output', choices=['console', 'file', 'both'], 
                       default='both', help='输出方式')
    
    args = parser.parse_args()
    
    monitor = UnifiedSitemapMonitor(base_url=args.base_url)
    
    if args.check_type == 'quick':
        report = monitor.run_quick_check()
    elif args.check_type == 'full':
        report = monitor.run_full_check()
    elif args.check_type == 'performance':
        report = monitor.run_performance_check()
    
    # 输出结果
    if args.output in ['console', 'both']:
        print(f"\n{'='*50}")
        print(f"Sitemap监控报告 - {args.check_type.upper()}")
        print(f"{'='*50}")
        print(f"健康度: {report['health_score']}%")
        print(f"检查时间: {report['timestamp']}")
        print(f"基础URL: {report['base_url']}")
        
        # 显示可用性结果
        availability = report['checks'].get('availability', {})
        if availability:
            print(f"\nSitemap可用性:")
            for url, result in availability.items():
                status = "✓" if result.get('status') == 'success' else "✗"
                response_time = result.get('response_time', 0)
                print(f"{status} {url} - {result.get('status', 'unknown')} ({response_time}s)")
    
    if args.output in ['file', 'both']:
        print(f"\n监控报告已保存到文件")
    
    print(f"\n监控完成！健康度: {report['health_score']}%")
    return report


if __name__ == '__main__':
    main()
