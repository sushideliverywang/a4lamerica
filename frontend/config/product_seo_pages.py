"""
产品SEO页面配置文件
管理所有动态产品SEO页面的定义，支持基于库存的自动页面管理
"""

from django.db.models import Q
from django.conf import settings

# 产品SEO页面配置
PRODUCT_SEO_PAGES = {
    'door-in-door-refrigerators-doraville': {
        'title': 'Best Door in Door Refrigerators in Doraville GA - Appliances 4 Less',
        'meta_description': 'Shop premium Door in Door refrigerators in Doraville, GA. Energy efficient models with ice makers, water dispensers. Same-day delivery available.',
        'h1_title': 'Door in Door Refrigerators in Doraville, Georgia',
        'short_title': 'Door in Door Refrigerators',
        'city_key': 'doraville',
        'show_on_homepage': True,
        'homepage_priority': 1,
        'active': True,

        # 产品筛选条件 - 支持多种筛选方式
        'filters': {
            # 基础筛选（必须）
            'basic': {
                'published': True,
                'order__isnull': True,
                'company_id': 'from_settings'  # 将从 settings.COMPANY_ID 获取
            },
            # 类别筛选（可选）
            #'category': {
            #    'names': ['French Door Refrigerator'],  # 按类别名称筛选
                # 'slugs': ['french-door-refrigerator'],  # 按类别slug筛选（可选）
            #},
            # 产品模型筛选（可选）
             'product_model': {
                 # 移除description查询，只使用型号匹配
                 'model_number__icontains': 'LH29S8565S, LRMDS3006S, LRMVC2306S',  # 按型号筛选
             },
            # 库存条件筛选（可选）
            # 'inventory': {
            #     'condition__in': ['BRAND_NEW', 'OPEN_BOX'],
            # }
        },
        'min_inventory': 1,  # 最少库存数量，低于此数量页面自动隐藏

        # SEO内容
        'keywords': [
            'door in door refrigerators doraville',
            'door in door fridge doraville ga',
            'counter depth door in door refrigerator',
            'energy star door in door refrigerator',
            'stainless steel door in door fridge'
        ],
        'content_description': 'Discover the perfect Door in Door refrigerator for your Doraville home. Our selection features energy-efficient models with spacious layouts, ice makers, and water dispensers.',
        'features': [
            'Energy Star certified models available',
            'Counter-depth and standard depth options',
            'Ice makers and water dispensers',
            'Stainless steel and black stainless finishes',
            'Same-day delivery in Doraville area'
        ],

        # 页面展示
        'featured_image': '/static/frontend/images/products/door-in-door-refrigerator.jpg',
        'background_image': '/static/frontend/images/city/Desktop-Doraville.webp',
        'icon': 'refrigerator',
    },

    'bespoke-kitchen-appliance-sets-chamblee': {
        'title': 'Bespoke Kitchen Appliance Sets Near Chamblee GA',
        'meta_description': 'Complete bespoke kitchen appliance packages in Chamblee. Matching refrigerator, stove, dishwasher sets. Professional installation available.',
        'h1_title': 'Bespoke Kitchen Appliance Sets in Chamblee',
        'short_title': 'Appliance Sets',
        'city_key': 'chamblee',
        'show_on_homepage': True,
        'homepage_priority': 2,
        'active': True,

        # 复杂筛选示例：通过产品描述查找不锈钢产品
        'filters': {
            'basic': {
                'published': True,
                'order__isnull': True,
                'company_id': 'from_settings'
            },
            #'category': {
            #    'names': ['Bespoke Kitchen Appliance Set']  # 厨房电器类别
            #},
            'product_model': {
                #'description__icontains': 'bespoke kitchen appliance set'  # 描述中包含不锈钢
                'model_number__icontains': 'RF23BB860012, NSI6DB990012, ME21DB670012, DW80BB707012'  # 按型号筛选
            }
        },
        'min_inventory': 1,  # 需要至少5件不同类型的产品才能组成套装1

        # SEO内容
        'keywords': [
            'bespoke kitchen appliance set chamblee',
            'kitchen appliance package chamblee ga',
            'matching kitchen appliances',
            'bespoke kitchen suite',
            'appliance bundle deals chamblee'
        ],
        'content_description': 'Create your dream kitchen with our bespoke appliance sets in Chamblee. Mix and match or choose complete packages for a coordinated look.',
        'features': [
            'Matching bespoke finishes',
            'Energy efficient appliances',
            'Package deals available',
            'Professional installation included',
            'Same brand coordination options'
        ],

        'featured_image': '/static/frontend/images/products/bespoke-kitchen-appliance-set.jpg',
        'background_image': '/static/frontend/images/city/Desktop-Chamblee.webp',
        'icon': 'appliance-set',
    },
}

def get_active_seo_pages():
    """
    获取所有激活的SEO页面配置

    Returns:
        dict: 激活的SEO页面配置字典
    """
    return {key: config for key, config in PRODUCT_SEO_PAGES.items()
            if config.get('active', True)}

def get_homepage_seo_pages():
    """
    获取需要在首页显示的SEO页面

    Returns:
        list: 按优先级排序的首页SEO页面列表
    """
    homepage_pages = []
    for key, config in get_active_seo_pages().items():
        if config.get('show_on_homepage', False):
            homepage_pages.append({
                'key': key,
                'config': config
            })

    # 按优先级排序
    homepage_pages.sort(key=lambda x: x['config'].get('homepage_priority', 999))
    return homepage_pages

def get_seo_page_config(page_key):
    """
    获取指定SEO页面的配置

    Args:
        page_key (str): SEO页面键名

    Returns:
        dict: SEO页面配置，如果不存在或未激活返回None
    """
    active_pages = get_active_seo_pages()
    return active_pages.get(page_key)

def build_product_filters(config):
    """
    根据配置构建Django QuerySet过滤条件

    支持新的filters结构：
    {
        'basic': {'published': True, 'company_id': 'from_settings'},
        'category': {'names': [...], 'slugs': [...]},
        'product_model': {'description__icontains': '...', 'model_numbers': [...]},
        'inventory': {'condition__in': [...]}
    }

    Args:
        config (dict): SEO页面配置

    Returns:
        Q: Django Q对象用于数据库查询
    """
    filters = Q()

    # 获取筛选配置
    filter_config = config.get('filters', {})

    # 基础筛选（必须）
    if 'basic' in filter_config:
        basic_filters = filter_config['basic']
        for field, value in basic_filters.items():
            if value == 'from_settings':
                # 从设置获取公司ID
                actual_value = getattr(settings, 'COMPANY_ID')
            else:
                actual_value = value
            filters &= Q(**{field: actual_value})

    # 类别筛选
    if 'category' in filter_config:
        category_config = filter_config['category']

        # 通过类别名称筛选
        if 'names' in category_config:
            filters &= Q(model_number__category__name__in=category_config['names'])

        # 通过类别slug筛选
        elif 'slugs' in category_config:
            filters &= Q(model_number__category__slug__in=category_config['slugs'])

    # 产品模型筛选
    if 'product_model' in filter_config:
        product_model_config = filter_config['product_model']
        product_model_filters = Q()

        for field, value in product_model_config.items():
            if field == 'model_numbers':
                # 特殊处理：支持多个型号的OR查询
                model_q = Q()
                for model_num in value:
                    model_q |= Q(model_number__model_number__icontains=model_num.strip())
                product_model_filters &= model_q
            elif field == 'model_number__icontains':
                # 处理逗号分隔的型号字符串
                if ',' in str(value):
                    model_numbers = [m.strip() for m in str(value).split(',')]
                    model_q = Q()
                    for model_num in model_numbers:
                        model_q |= Q(model_number__model_number__icontains=model_num)
                    product_model_filters &= model_q
                else:
                    product_model_filters &= Q(model_number__model_number__icontains=value)
            else:
                product_model_filters &= Q(**{f'model_number__{field}': value})

        filters &= product_model_filters

    # 库存条件筛选
    if 'inventory' in filter_config:
        inventory_config = filter_config['inventory']
        for field, value in inventory_config.items():
            filters &= Q(**{field: value})

    return filters

# SEO页面的URL slug到配置的映射
SEO_PAGE_SLUGS = {key: key for key in PRODUCT_SEO_PAGES.keys()}