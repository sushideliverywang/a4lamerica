"""
生成和验证网站地图的管理命令
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.test import RequestFactory
from django.contrib.sitemaps.views import sitemap
from frontend.views import sitemaps
from django.conf import settings
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin


class Command(BaseCommand):
    help = '生成和验证网站地图。在生产环境中会自动使用 settings.SITE_URL，开发环境可手动指定 --base-url 参数'

    def add_arguments(self, parser):
        parser.add_argument(
            '--validate',
            action='store_true',
            help='验证sitemap XML格式',
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default=None,  # 默认从settings获取
            help='基础URL用于验证（默认从settings.SITE_URL获取）',
        )

    def handle(self, *args, **options):
        # 如果没有指定base_url，则从settings获取
        base_url = options['base_url']
        if not base_url:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        
        validate = options['validate']
        
        # 显示当前环境信息
        environment = "生产环境" if not settings.DEBUG else "开发环境"
        self.stdout.write(
            self.style.SUCCESS(f'开始生成网站地图... ({environment}, 使用域名: {base_url})')
        )
        
        # 生成各个sitemap
        sitemap_urls = [
            f'{base_url}/sitemap.xml',
            f'{base_url}/sitemap-static.xml',
            f'{base_url}/sitemap-stores.xml',
            f'{base_url}/sitemap-categories.xml',
            f'{base_url}/sitemap-products.xml',
            f'{base_url}/sitemap-warranty.xml',
            f'{base_url}/sitemap-terms.xml',
        ]
        
        for url in sitemap_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {url} - 成功生成')
                    )
                    
                    if validate:
                        self.validate_sitemap_xml(response.text, url)
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {url} - HTTP {response.status_code}')
                    )
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ {url} - 请求失败: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n网站地图生成完成！')
        )

    def validate_sitemap_xml(self, xml_content, url):
        """验证sitemap XML格式"""
        try:
            root = ET.fromstring(xml_content)
            
            # 检查根元素
            if root.tag == 'urlset':
                # 验证URL元素
                urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                self.stdout.write(f'  - 包含 {len(urls)} 个URL')
                
                # 检查必需的字段
                for i, url_elem in enumerate(urls[:5]):  # 只检查前5个
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        self.stdout.write(f'  - URL {i+1}: {loc.text}')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  - URL {i+1}: 缺少loc元素')
                        )
                        
            elif root.tag == 'sitemapindex':
                # 验证sitemap索引
                sitemaps = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
                self.stdout.write(f'  - 包含 {len(sitemaps)} 个子sitemap')
                
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ XML格式验证通过')
            )
            
        except ET.ParseError as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ XML格式错误: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ 验证失败: {e}')
            )
