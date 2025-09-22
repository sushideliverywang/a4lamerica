"""
管理命令：检查SEO页面状态
用于验证SEO页面配置和库存状况
"""

from django.core.management.base import BaseCommand
from django.urls import reverse
from frontend.config.product_seo_pages import (
    get_active_seo_pages, get_homepage_seo_pages, build_product_filters
)
from frontend.models_proxy import InventoryItem


class Command(BaseCommand):
    help = 'Check SEO pages status and inventory counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--homepage-only',
            action='store_true',
            help='Only check pages configured for homepage display',
        )
        parser.add_argument(
            '--check-urls',
            action='store_true',
            help='Test URL generation for all pages',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== SEO Pages Status Check ===\n')
        )

        if options['homepage_only']:
            pages_to_check = get_homepage_seo_pages()
            self.stdout.write('Checking homepage SEO pages only...\n')
        else:
            active_pages = get_active_seo_pages()
            pages_to_check = [{'key': key, 'config': config}
                            for key, config in active_pages.items()]
            self.stdout.write('Checking all active SEO pages...\n')

        # 检查每个页面的状态
        for page_data in pages_to_check:
            if 'key' in page_data:
                page_key = page_data['key']
                page_config = page_data['config']
            else:
                page_key = page_data
                page_config = get_active_seo_pages()[page_key]

            self.check_page_status(page_key, page_config, options['check_urls'])

        self.stdout.write(
            self.style.SUCCESS('\n=== Check Complete ===')
        )

    def check_page_status(self, page_key, page_config, check_urls=False):
        """检查单个页面的状态"""
        self.stdout.write(f"\n📄 {page_key}")
        self.stdout.write(f"   Title: {page_config.get('title', 'No title')}")
        self.stdout.write(f"   Short Title: {page_config.get('short_title', 'No short title')}")
        self.stdout.write(f"   City: {page_config.get('city_key', 'No city')}")
        self.stdout.write(f"   Homepage Display: {page_config.get('show_on_homepage', False)}")
        self.stdout.write(f"   Active: {page_config.get('active', True)}")

        # 检查库存数量
        try:
            filters = build_product_filters(page_config)
            item_count = InventoryItem.objects.filter(filters).count()
            min_inventory = page_config.get('min_inventory', 1)

            if item_count >= min_inventory:
                status_icon = "✅"
                status_text = "SUFFICIENT"
            else:
                status_icon = "⚠️"
                status_text = "INSUFFICIENT"

            self.stdout.write(f"   Inventory: {status_icon} {item_count} items ({status_text})")
            self.stdout.write(f"   Min Required: {min_inventory}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   Inventory: ❌ ERROR - {str(e)}")
            )

        # 检查URL生成
        if check_urls:
            try:
                url = reverse('frontend:product_seo_page', kwargs={'seo_page_key': page_key})
                self.stdout.write(f"   URL: ✅ {url}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   URL: ❌ ERROR - {str(e)}")
                )

        # 检查筛选配置
        filters_config = page_config.get('filters', {})
        if 'basic' in filters_config:
            self.stdout.write(f"   Basic Filters: ✅ Configured")
        else:
            self.stdout.write(f"   Basic Filters: ⚠️ Missing")

        if 'category' in filters_config or 'product_model' in filters_config:
            self.stdout.write(f"   Product Filters: ✅ Configured")
        else:
            self.stdout.write(f"   Product Filters: ⚠️ Missing")