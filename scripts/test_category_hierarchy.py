#!/usr/bin/env python
"""
测试类别层级结构和子类别查询功能
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a4lamerica.settings')
django.setup()

from frontend.models_proxy import Category
from frontend.config.product_seo_pages import get_category_with_descendants


def display_category_tree(category, level=0):
    """
    递归显示类别树结构

    Args:
        category: Category对象
        level: 当前层级（用于缩进）
    """
    indent = "  " * level
    print(f"{indent}├─ {category.name} (ID: {category.id})")

    # 递归显示子类别
    subcategories = category.subcategories.all()
    for sub in subcategories:
        display_category_tree(sub, level + 1)


def main():
    print("\n" + "="*80)
    print("类别层级结构和子类别查询测试")
    print("="*80 + "\n")

    # 1. 显示所有顶级类别
    print("1. 所有顶级类别（没有父类别）:")
    print("-" * 80)
    top_categories = Category.objects.filter(parent_category__isnull=True)

    if not top_categories.exists():
        print("   未找到顶级类别")
    else:
        for cat in top_categories:
            display_category_tree(cat)
    print()

    # 2. 测试 get_category_with_descendants 函数
    print("\n2. 测试 get_category_with_descendants 函数:")
    print("-" * 80)

    # 找一个有子类别的类别进行测试
    test_category_names = ['Dishwasher', 'Refrigerator', 'Washer', 'Dryer']
    for cat_name in test_category_names:
        try:
            category = Category.objects.get(name=cat_name)
            print(f"\n测试类别: {category.name}")

            # 获取所有子孙类别ID
            descendant_ids = get_category_with_descendants(category)
            print(f"   包含的类别ID数量: {len(descendant_ids)}")
            print(f"   类别ID列表: {descendant_ids}")

            # 显示所有子孙类别的名称
            all_categories = Category.objects.filter(id__in=descendant_ids)
            print(f"   包含的类别名称:")
            for cat in all_categories:
                parent_info = f" (子类别 of {cat.parent_category.name})" if cat.parent_category else " (顶级类别)"
                print(f"     - {cat.name}{parent_info}")

        except Category.DoesNotExist:
            print(f"   类别 '{cat_name}' 不存在")
            continue

    # 3. 显示所有类别的父子关系
    print("\n\n3. 所有类别的父子关系:")
    print("-" * 80)
    all_categories = Category.objects.all().order_by('name')

    for cat in all_categories:
        if cat.parent_category:
            print(f"{cat.name} → 父类别: {cat.parent_category.name}")
        else:
            print(f"{cat.name} → 顶级类别")

        # 显示子类别
        subcats = cat.subcategories.all()
        if subcats.exists():
            subcat_names = [s.name for s in subcats]
            print(f"  └─ 子类别: {', '.join(subcat_names)}")

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
