from django.core.management.base import BaseCommand
from inventory.models import InventoryItem
from frontend.utils import cache_item_hash, encode_item_id


class Command(BaseCommand):
    help = '缓存所有已发布商品的哈希编码以提高性能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新缓存所有商品哈希',
        )

    def handle(self, *args, **options):
        self.stdout.write('开始缓存商品哈希编码...')
        
        # 获取所有已发布的商品，且状态为可销售状态
        items = InventoryItem.objects.filter(
            published=True,
            current_state_id__in=[4, 5, 8]  # 只显示这三种状态的商品
        )
        total_items = items.count()
        
        self.stdout.write(f'找到 {total_items} 个已发布的商品')
        
        cached_count = 0
        for i, item in enumerate(items, 1):
            try:
                # 缓存商品哈希
                cache_item_hash(item)
                cached_count += 1
                
                # 显示进度
                if i % 100 == 0:
                    self.stdout.write(f'已处理 {i}/{total_items} 个商品')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'缓存商品 {item.id} 时出错: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功缓存了 {cached_count}/{total_items} 个商品的哈希编码'
            )
        )
        
        # 显示一些示例哈希
        self.stdout.write('\n示例哈希编码:')
        for item in items[:5]:
            hash_value = encode_item_id(item.id)
            self.stdout.write(f'商品 {item.id} -> {hash_value}') 