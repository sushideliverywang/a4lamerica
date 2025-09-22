"""
管理命令：测试sitemap配置
验证所有sitemap是否正常工作，特别是新的ProductSEOPageSitemap
"""

from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import RequestFactory
from frontend.views import sitemaps, sitemap_view
from frontend.sitemaps import ProductSEOPageSitemap


class Command(BaseCommand):
    help = 'Test sitemap configuration and URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--section',
            type=str,
            help='Test specific sitemap section (e.g., seo_products)',
        )
        parser.add_argument(
            '--check-urls',
            action='store_true',
            help='Test URL generation for sitemap entries',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Sitemap Configuration Test ===\n')
        )

        if options['section']:
            # 测试特定section
            self.test_section(options['section'], options['check_urls'])
        else:
            # 测试所有sections
            self.test_all_sections(options['check_urls'])

        self.stdout.write(
            self.style.SUCCESS('\n=== Test Complete ===')
        )

    def test_all_sections(self, check_urls=False):
        """测试所有sitemap sections"""
        self.stdout.write("Testing all sitemap sections...\n")

        for section_name, sitemap_class in sitemaps.items():
            self.test_section(section_name, check_urls)

    def test_section(self, section_name, check_urls=False):
        """测试单个sitemap section"""
        self.stdout.write(f"\n📍 Testing section: {section_name}")

        if section_name not in sitemaps:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Section '{section_name}' not found in sitemaps")
            )
            return

        sitemap_class = sitemaps[section_name]

        try:
            # 实例化sitemap
            sitemap_instance = sitemap_class()
            self.stdout.write(f"   ✅ Sitemap class instantiated: {sitemap_class.__name__}")

            # 获取items
            items = list(sitemap_instance.items())
            item_count = len(items)
            self.stdout.write(f"   📊 Items count: {item_count}")

            if item_count == 0:
                self.stdout.write(f"   ⚠️  No items found")
                return

            # 测试前几个items的URL生成
            test_items = items[:3]  # 只测试前3个
            for i, item in enumerate(test_items):
                try:
                    url = sitemap_instance.location(item)
                    priority = sitemap_instance.priority(item) if hasattr(sitemap_instance, 'priority') and callable(getattr(sitemap_instance, 'priority')) else sitemap_instance.priority
                    changefreq = sitemap_instance.changefreq(item) if hasattr(sitemap_instance, 'changefreq') and callable(getattr(sitemap_instance, 'changefreq')) else sitemap_instance.changefreq

                    self.stdout.write(f"   📝 Item {i+1}: {url}")
                    self.stdout.write(f"      Priority: {priority}, Changefreq: {changefreq}")

                    if check_urls:
                        # 测试URL是否可以生成响应
                        self.test_url_response(url)

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error generating URL for item {i+1}: {str(e)}")
                    )

            # 特殊测试ProductSEOPageSitemap
            if section_name == 'seo_products':
                self.test_seo_products_special(sitemap_instance, items)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error testing section: {str(e)}")
            )

    def test_seo_products_special(self, sitemap_instance, items):
        """特殊测试ProductSEOPageSitemap的功能"""
        self.stdout.write(f"   🔍 Special tests for ProductSEOPageSitemap:")

        if items:
            # 测试第一个item的详细信息
            first_item = items[0]
            try:
                config = first_item['config']
                item_count = first_item['item_count']
                page_key = first_item['page_key']

                self.stdout.write(f"      📄 Page: {page_key}")
                self.stdout.write(f"      📊 Inventory: {item_count} items")
                self.stdout.write(f"      🏠 Homepage: {config.get('show_on_homepage', False)}")
                self.stdout.write(f"      📍 City: {config.get('city_key', 'N/A')}")

                # 测试动态优先级和changefreq
                priority = sitemap_instance.priority(first_item)
                changefreq = sitemap_instance.changefreq(first_item)
                self.stdout.write(f"      ⭐ Dynamic Priority: {priority}")
                self.stdout.write(f"      🔄 Dynamic Changefreq: {changefreq}")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"      ❌ Error in special tests: {str(e)}")
                )

    def test_url_response(self, url):
        """测试URL是否可以正常响应（简单检查）"""
        try:
            # 这里只是检查URL格式，不实际发送请求
            if url.startswith('/'):
                self.stdout.write(f"      ✅ URL format valid")
            else:
                self.stdout.write(f"      ⚠️  URL format unusual: {url}")
        except Exception as e:
            self.stdout.write(f"      ❌ URL test error: {str(e)}")

    def test_sitemap_index(self):
        """测试sitemap索引页面"""
        self.stdout.write("\n🗺️  Testing sitemap index...")

        try:
            factory = RequestFactory()
            request = factory.get('/sitemap.xml')

            response = sitemap_view(request)
            self.stdout.write(f"   ✅ Sitemap index response status: {response.status_code}")

            if hasattr(response, 'content'):
                content_preview = response.content[:200].decode('utf-8', errors='ignore')
                self.stdout.write(f"   📄 Content preview: {content_preview}...")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error testing sitemap index: {str(e)}")
            )