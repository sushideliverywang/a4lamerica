#!/usr/bin/env python
"""
SEO页面产品查询诊断脚本

检查指定SEO页面的筛选条件是否能查到可用的库存商品
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a4lamerica.settings')
django.setup()

from django.conf import settings
from django.db.models import Q
from frontend.models_proxy import InventoryItem, ProductModel, Brand, Category
from frontend.config.product_seo_pages import get_seo_page_config, build_product_filters


def check_seo_page(page_key):
    """
    检查指定SEO页面的产品筛选结果

    Args:
        page_key: SEO页面的key，如 'lg-truesteam-dishwasher-norcross'
    """
    print(f"\n{'='*80}")
    print(f"检查 SEO 页面: {page_key}")
    print(f"{'='*80}\n")

    # 获取配置
    config = get_seo_page_config(page_key)
    if not config:
        print(f"❌ 错误: 找不到SEO页面配置 '{page_key}'")
        return

    print(f"✓ 页面标题: {config.get('title')}")
    print(f"✓ 简短标题: {config.get('short_title')}")
    print(f"✓ 城市: {config.get('city_key')}")
    print(f"✓ 最少库存: {config.get('min_inventory', 1)}")
    print()

    # 显示筛选条件
    print("筛选条件:")
    print("-" * 80)
    filters_config = config.get('filters', {})

    for filter_type, filter_data in filters_config.items():
        print(f"\n{filter_type.upper()}:")
        if isinstance(filter_data, dict):
            for key, value in filter_data.items():
                print(f"  - {key}: {value}")

    print(f"\n{'='*80}\n")

    # 构建筛选器
    try:
        filters = build_product_filters(config)
        print("✓ 筛选器构建成功")
    except Exception as e:
        print(f"❌ 筛选器构建失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n生成的Django Q对象:")
    print(f"  {filters}")
    print()

    # 分步检查各个筛选条件
    print(f"\n{'='*80}")
    print("分步检查筛选条件")
    print(f"{'='*80}\n")

    # 1. 检查所有库存
    total_inventory = InventoryItem.objects.all().count()
    print(f"1. 总库存数量: {total_inventory}")

    # 2. 检查已发布的库存
    published_items = InventoryItem.objects.filter(published=True)
    print(f"2. 已发布库存: {published_items.count()}")

    # 3. 检查未售出的库存
    available_items = published_items.filter(order__isnull=True)
    print(f"3. 已发布且未售出: {available_items.count()}")

    # 4. 检查公司筛选
    company_id = getattr(settings, 'COMPANY_ID', None)
    print(f"4. 公司ID (从settings): {company_id}")
    if company_id:
        company_items = available_items.filter(company_id=company_id)
        print(f"   符合公司条件: {company_items.count()}")
    else:
        company_items = available_items
        print(f"   ⚠️  未设置COMPANY_ID")

    # 5. 检查类别筛选
    if 'category' in filters_config:
        category_config = filters_config['category']
        if 'names' in category_config:
            category_names = category_config['names']
            print(f"\n5. 类别筛选: {category_names}")

            # 显示所有可用的类别
            all_categories = Category.objects.all().values_list('name', flat=True)
            print(f"   数据库中所有类别: {list(all_categories)}")

            # 检查类别是否存在
            matching_categories = Category.objects.filter(name__in=category_names)
            print(f"   匹配的类别: {list(matching_categories.values_list('name', flat=True))}")

            category_items = company_items.filter(model_number__category__name__in=category_names)
            print(f"   符合类别条件: {category_items.count()}")

            if category_items.count() > 0:
                print(f"   示例产品型号:")
                for item in category_items[:3]:
                    print(f"     - {item.model_number.brand.name} {item.model_number.model_number}")
    else:
        category_items = company_items

    # 6. 检查品牌筛选
    if 'brand' in filters_config:
        brand_config = filters_config['brand']
        print(f"\n6. 品牌筛选: {brand_config}")

        # 显示所有可用的品牌
        all_brands = Brand.objects.all().values_list('name', flat=True)
        print(f"   数据库中所有品牌: {list(all_brands)}")

        # 构建品牌查询
        brand_q = Q()
        for field, value in brand_config.items():
            brand_q &= Q(**{f'model_number__brand__{field}': value})

        brand_items = category_items.filter(brand_q)
        print(f"   符合品牌条件: {brand_items.count()}")

        if brand_items.count() > 0:
            print(f"   示例产品型号:")
            for item in brand_items[:3]:
                print(f"     - {item.model_number.brand.name} {item.model_number.model_number}")
    else:
        brand_items = category_items

    # 7. 检查产品模型筛选（description）
    if 'product_model' in filters_config:
        pm_config = filters_config['product_model']
        print(f"\n7. 产品模型筛选: {pm_config}")

        if 'description__icontains' in pm_config:
            keyword = pm_config['description__icontains']
            print(f"   描述关键字: '{keyword}'")

            # 显示所有符合品牌和类别的ProductModel的描述
            product_models = ProductModel.objects.filter(
                inventoryitem__in=brand_items
            ).distinct()

            print(f"\n   当前筛选下的产品型号数量: {product_models.count()}")
            print(f"   产品描述示例:")
            for pm in product_models[:5]:
                desc = pm.description[:100] if pm.description else "[无描述]"
                has_keyword = keyword.lower() in (pm.description or "").lower()
                marker = "✓" if has_keyword else "✗"
                print(f"     {marker} {pm.brand.name} {pm.model_number}: {desc}...")

            # 检查包含关键字的产品
            keyword_items = brand_items.filter(model_number__description__icontains=keyword)
            print(f"\n   符合描述关键字条件: {keyword_items.count()}")

            if keyword_items.count() > 0:
                print(f"   匹配的产品:")
                for item in keyword_items[:5]:
                    print(f"     - {item.model_number.brand.name} {item.model_number.model_number}")
                    print(f"       描述: {item.model_number.description[:150]}...")
    else:
        keyword_items = brand_items

    # 8. 最终结果
    print(f"\n{'='*80}")
    print("最终筛选结果")
    print(f"{'='*80}\n")

    try:
        final_items = InventoryItem.objects.filter(filters).distinct()
        print(f"✓ 符合所有条件的库存数量: {final_items.count()}")

        if final_items.count() > 0:
            print(f"\n找到的产品:")
            for item in final_items[:10]:
                print(f"\n  控制号: {item.control_number}")
                print(f"  品牌: {item.model_number.brand.name}")
                print(f"  型号: {item.model_number.model_number}")
                print(f"  类别: {item.model_number.category.name}")
                print(f"  描述: {item.model_number.description[:100]}...")
                print(f"  零售价: ${item.retail_price}")
                print(f"  已发布: {item.published}")
                print(f"  订单: {item.order}")
        else:
            print("\n❌ 未找到符合条件的产品")
            print("\n可能的原因:")
            print("1. 数据库中没有符合所有筛选条件的产品")
            print("2. 产品型号的description字段不包含关键字")
            print("3. 品牌或类别名称不匹配")
            print("4. 所有符合条件的产品都已售出或未发布")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()


def list_all_seo_pages():
    """列出所有可用的SEO页面"""
    from frontend.config.product_seo_pages import PRODUCT_SEO_PAGES

    print("\n可用的SEO页面:")
    print("=" * 80)
    for key, config in PRODUCT_SEO_PAGES.items():
        active = "✓" if config.get('active', True) else "✗"
        on_homepage = "首页" if config.get('show_on_homepage', False) else ""
        print(f"{active} {key:50s} {on_homepage}")
        print(f"   {config.get('short_title', '')}")
    print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='检查SEO页面的产品筛选结果')
    parser.add_argument('page_key', nargs='?', help='SEO页面的key，如 lg-truesteam-dishwasher-norcross')
    parser.add_argument('--list', action='store_true', help='列出所有SEO页面')

    args = parser.parse_args()

    if args.list:
        list_all_seo_pages()
    elif args.page_key:
        check_seo_page(args.page_key)
    else:
        # 默认检查新添加的页面
        print("未指定页面，检查默认页面: lg-truesteam-dishwasher-norcross")
        print("使用 --list 查看所有可用页面")
        check_seo_page('lg-truesteam-dishwasher-norcross')
