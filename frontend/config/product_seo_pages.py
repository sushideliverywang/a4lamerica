"""
产品SEO页面配置文件
管理所有动态产品SEO页面的定义，支持基于库存的自动页面管理
"""

from django.db.models import Q
from django.conf import settings

# ==================== 产品SEO页面通用模板 ====================
# 复制此模板来创建新的SEO页面，根据注释修改相应内容

PRODUCT_SEO_PAGE_TEMPLATE = {
    # 页面标识符：使用产品类型-城市名称的格式，全小写，用连字符分隔
    # 例如：'washing-machines-atlanta', 'kitchen-appliances-duluth'
    'product-category-city-name': {

        # === 基础SEO信息 ===
        'title': 'Best [Product Category] in [City Name] GA - Appliances 4 Less',
        # 页面标题，显示在浏览器标签栏和搜索结果中，建议60字符以内
        # 例如：'Best Washing Machines in Atlanta GA - Appliances 4 Less'

        'meta_description': 'Shop premium [product category] in [City], GA. [Key features]. Same-day delivery available.',
        # 页面描述，显示在搜索结果中，建议150-160字符以内
        # 例如：'Shop premium washing machines in Atlanta, GA. Energy efficient models with smart features. Same-day delivery available.'

        'h1_title': '[Product Category] in [City Name], Georgia',
        # 页面主标题，显示在页面顶部
        # 例如：'Washing Machines in Atlanta, Georgia'

        'short_title': '[Product Category]',
        # 简短标题，用于导航和卡片显示
        # 例如：'Washing Machines'

        # === 地理位置信息 ===
        'city_key': 'city_name',
        # 城市标识符，必须与CITIES配置中的key匹配
        # 例如：'atlanta', 'doraville', 'chamblee'

        # === 首页显示设置 ===
        'show_on_homepage': True,
        # 是否在首页显示此SEO页面，True或False

        'homepage_priority': 1,
        # 首页显示优先级，数字越小优先级越高（1最高）

        'active': True,
        # 页面是否激活，False则不会显示此页面

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,              # 只显示已发布的产品
                'order__isnull': True,          # 只显示未售出的产品
                'company_id': 'from_settings'   # 自动从settings获取公司ID
            },

            # 类别筛选（可选）- 二选一使用
            # 注意：会自动包含所有子类别！例如 'Dishwasher' 会匹配所有洗碗机子类别
            # 'category': {
            #     'names': ['Category Name 1', 'Category Name 2'],  # 按类别名称筛选（自动包含子类别）
            #     # 或者使用slug筛选：
            #     # 'slugs': ['category-slug-1', 'category-slug-2'],  # 按类别slug筛选（自动包含子类别）
            # },

            # 产品模型筛选（推荐使用）
            'product_model': {
                # 按型号筛选（推荐）- 支持逗号分隔多个型号
                'model_number__icontains': 'MODEL1, MODEL2, MODEL3',
                # 例如：'WF45T6000AW, WF45T6200AW, WF50T8500AV'

                # 或者按描述筛选（可选）
                # 'description__icontains': 'keyword in description',
            },

            # 库存条件筛选（可选）
            # 'inventory': {
            #     'condition__in': ['BRAND_NEW', 'OPEN_BOX'],  # 只显示特定条件的产品
            # }
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'product category city name',      # 主关键词
            'product category city name ga',   # 带州名的关键词
            'specific feature keyword',        # 特定功能关键词
            'brand related keyword',           # 品牌相关关键词
            'local service keyword'            # 本地服务关键词
        ],
        # 例如：['washing machines atlanta', 'washers atlanta ga', 'front load washers', 'samsung lg washers', 'washer delivery atlanta']

        # === 页面内容 ===
        'content_description': 'Discover the perfect [product category] for your [city] home. Our selection features [key features and benefits].',
        # 页面内容描述，显示在页面中
        # 例如：'Discover the perfect washing machine for your Atlanta home. Our selection features energy-efficient models with smart technology and large capacity.'

        'features': [
            'Feature 1 description',           # 产品特色1
            'Feature 2 description',           # 产品特色2
            'Feature 3 description',           # 产品特色3
            'Feature 4 description',           # 产品特色4
            'Local service description'        # 本地服务特色
        ],
        # 例如：['Energy Star certified models', 'Smart WiFi connectivity', 'Large capacity options', 'Quiet operation technology', 'Same-day delivery in Atlanta']

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/product-category-image.jpg',
        # 产品特色图片路径，显示在首页卡片中
        # 建议尺寸：600x400px，例如：'/static/frontend/images/products/washing-machines.jpg'

        'background_image': '/static/frontend/images/city/Desktop-CityName.webp',
        # 城市背景图片路径，显示在产品页面中
        # 例如：'/static/frontend/images/city/Desktop-Atlanta.webp'

        'icon': 'icon-name',
        # 图标标识符，用于显示SVG图标（如果没有图片时）
        # 可选值：'refrigerator', 'washing-machine', 'appliance-set', 'discount' 等
    },
}

# ==================== 实际使用的SEO页面配置 ====================
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
                 'model_number__icontains': 'LH29S8565S, LRMDS3006S, LRMVC2306S, LRMVS3006S, LH29S8250S, LH29S8365S',  # 按型号筛选
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

    'bespoke-refrigerators-chamblee': {
        'title': 'Bespoke Refrigerator in Chamblee GA - Appliances 4 Less',
        'meta_description': 'Complete bespoke Refrigerator in Chamblee. Matching refrigerator, stove, dishwasher sets. Professional installation available.',
        'h1_title': 'Bespoke Refrigerator in Chamblee, Georgia',
        'short_title': 'Bespoke Refrigerator',
        'city_key': 'chamblee',
        'show_on_homepage': True,
        'homepage_priority': 2,
        'active': True,
        'filters': {
            'basic': {
                'published': True,
                'order__isnull': True,
                'company_id': 'from_settings'
            },
            'category': {
                'names': ['Bespoke Refrigerator']
            },
        },
        'min_inventory': 1,
        'keywords': [
        'bespoke refrigerator chamblee',
        'bespoke refrigerator chamblee ga',
        'FAMILY HUB refrigerator',
        ],
        'content_description': 'Create your dream kitchen with our bespoke refrigerator in Chamblee. Mix and match or choose complete packages for a coordinated look.',
        'features': [
            'Energy efficient refrigerator',
            'FAMILY HUB refrigerator',
        ],
        'featured_image': '/static/frontend/images/products/bespoke-refrigerators.webp',
        'background_image': '/static/frontend/images/city/Desktop-Chamblee.webp',
        'icon': 'refrigerator',
    },

    'bosch-800-series-dishwashers-duluth': {

        # === 基础SEO信息 ===
        'title': 'Most Quiet Dishwashers in Duluth GA - Appliances 4 Less',
        # 页面标题，显示在浏览器标签栏和搜索结果中，建议60字符以内
        # 例如：'Best Washing Machines in Atlanta GA - Appliances 4 Less'

        'meta_description': 'Shop premium Bosch 800 series dishwashers in Duluth, GA. 42dB noise level. Same-day delivery subject to availability.',
        # 页面描述，显示在搜索结果中，建议150-160字符以内
        # 例如：'Shop premium washing machines in Atlanta, GA. Energy efficient models with smart features. Same-day delivery available.'

        'h1_title': 'Bosch 800 series Dishwashers in Duluth, Georgia',
        # 页面主标题，显示在页面顶部
        # 例如：'Washing Machines in Atlanta, Georgia'

        'short_title': 'Bosch 800 series Dishwashers',
        # 简短标题，用于导航和卡片显示
        # 例如：'Washing Machines'

        # === 地理位置信息 ===
        'city_key': 'duluth',
        # 城市标识符，必须与CITIES配置中的key匹配
        # 例如：'atlanta', 'doraville', 'chamblee'

        # === 首页显示设置 ===
        'show_on_homepage': False,
        # 是否在首页显示此SEO页面，True或False

        'homepage_priority': 3,
        # 首页显示优先级，数字越小优先级越高（1最高）

        'active': True,
        # 页面是否激活，False则不会显示此页面

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,              # 只显示已发布的产品
                'order__isnull': True,          # 只显示未售出的产品
                'company_id': 'from_settings'   # 自动从settings获取公司ID
            },

            # 类别筛选（可选）- 二选一使用
            # 注意：会自动包含所有子类别！例如 'Dishwasher' 会匹配所有洗碗机子类别
            # 'category': {
            #     'names': ['Category Name 1', 'Category Name 2'],  # 按类别名称筛选（自动包含子类别）
            #     # 或者使用slug筛选：
            #     # 'slugs': ['category-slug-1', 'category-slug-2'],  # 按类别slug筛选（自动包含子类别）
            # },

            # 产品模型筛选（推荐使用）
            'product_model': {
                # 按型号筛选（推荐）- 支持逗号分隔多个型号
                'model_number__icontains': 'SHX78CC5UC, SHP9PCM5N',
                # 例如：'WF45T6000AW, WF45T6200AW, WF50T8500AV'

                # 或者按描述筛选（可选）
                # 'description__icontains': 'keyword in description',
            },

            # 库存条件筛选（可选）
            # 'inventory': {
            #     'condition__in': ['BRAND_NEW', 'OPEN_BOX'],  # 只显示特定条件的产品
            # }
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'bosch 800 series dishwashers duluth',      # 主关键词
            'bosch 800 series dishwasher duluth ga',   # 带州名的关键词
            'quiet dishwasher duluth ga',        # 特定功能关键词
            'energy star dishwasher duluth ga',           # 品牌相关关键词
            'dishwasher installation duluth ga'            # 本地服务关键词
        ],
        # 例如：['washing machines atlanta', 'washers atlanta ga', 'front load washers', 'samsung lg washers', 'washer delivery atlanta']

        # === 页面内容 ===
        'content_description': 'Discover the perfect Bosch 800 series dishwasher for your Duluth home. Our selection features energy-efficient models with quiet operation technology.',
        # 页面内容描述，显示在页面中
        # 例如：'Discover the perfect washing machine for your Atlanta home. Our selection features energy-efficient models with smart technology and large capacity.'

        'features': [
            'The deepest clean from PrecisionWash® with PowerControl',           # 产品特色1
            'The ultimate dry with CrystalDry',           # 产品特色2
            'Newly redesigned EasyGlide rack system for a smooth glide on all three racks',           # 产品特色3
            'Enhance your cleaning experience with Wi-Fi enabled Home Connect',           # 产品特色4
            'FREE delivery in Duluth area'        # 本地服务特色
        ],
        # 例如：['Energy Star certified models', 'Smart WiFi connectivity', 'Large capacity options', 'Quiet operation technology', 'Same-day delivery in Atlanta']

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/bosch-800-series-dishwasher.webp',
        # 产品特色图片路径，显示在首页卡片中
        # 建议尺寸：600x400px，例如：'/static/frontend/images/products/washing-machines.jpg'

        'background_image': '/static/frontend/images/city/Desktop-Duluth.webp',
        # 城市背景图片路径，显示在产品页面中
        # 例如：'/static/frontend/images/city/Desktop-Atlanta.webp'

        'icon': 'dishwasher',
        # 图标标识符，用于显示SVG图标（如果没有图片时）
        # 可选值：'refrigerator', 'washing-machine', 'appliance-set', 'discount' 等
    },

    'all-in-one-washer-dryer-sandy-springs': {

        # === 基础SEO信息 ===
        'title': 'Best All-in-One Washer Dryer in Sandy Springs GA - Appliances 4 Less',
        # 页面标题，显示在浏览器标签栏和搜索结果中，建议60字符以内
        # 例如：'Best Washing Machines in Atlanta GA - Appliances 4 Less'

        'meta_description': 'Shop premium All-in-One washer dryer in Sandy Springs, GA. Apartment friendly. Same-day delivery subject to availability.',
        # 页面描述，显示在搜索结果中，建议150-160字符以内
        # 例如：'Shop premium washing machines in Atlanta, GA. Energy efficient models with smart features. Same-day delivery available.'

        'h1_title': 'All-in-One Washer Dryer in Sandy Springs, Georgia',
        # 页面主标题，显示在页面顶部
        # 例如：'Washing Machines in Atlanta, Georgia'

        'short_title': 'All-in-One Washer Dryer',
        # 简短标题，用于导航和卡片显示
        # 例如：'Washing Machines'

        # === 地理位置信息 ===
        'city_key': 'sandy_springs',
        # 城市标识符，必须与CITIES配置中的key匹配
        # 例如：'atlanta', 'doraville', 'chamblee'

        # === 首页显示设置 ===
        'show_on_homepage': True,
        # 是否在首页显示此SEO页面，True或False

        'homepage_priority': 4,
        # 首页显示优先级，数字越小优先级越高（1最高）

        'active': True,
        # 页面是否激活，False则不会显示此页面

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,              # 只显示已发布的产品
                'order__isnull': True,          # 只显示未售出的产品
                'company_id': 'from_settings'   # 自动从settings获取公司ID
            },

            # 类别筛选（可选）- 二选一使用
             'category': {
                 'names': ['Washer/Dryer Combo'],  # 按类别名称筛选
                 # 或者使用slug筛选：
                 # 'slugs': ['category-slug-1', 'category-slug-2'],
            },

            # 产品模型筛选（推荐使用）
            #'product_model': {
                # 按型号筛选（推荐）- 支持逗号分隔多个型号
                #'model_number__icontains': 'MODEL1, MODEL2, MODEL3',
                # 例如：'WF45T6000AW, WF45T6200AW, WF50T8500AV'

                # 或者按描述筛选（可选）
                # 'description__icontains': 'keyword in description',
            #},

            # 库存条件筛选（可选）
            # 'inventory': {
            #     'condition__in': ['BRAND_NEW', 'OPEN_BOX'],  # 只显示特定条件的产品
            # }
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'all-in-one washer dryer sandy springs',      # 主关键词
            'all-in-one washer dryer sandy springs georgia',   # 带州名的关键词
            'mega capacity lets you fit more in every load',        # 特定功能关键词
            'lg and samsung all-in-one washer dryer',            # 品牌相关关键词
            'sandy springs apartment friendly'            # 本地服务关键词
        ],
        # 例如：['washing machines atlanta', 'washers atlanta ga', 'front load washers', 'samsung lg washers', 'washer delivery atlanta']

        # === 页面内容 ===
        'content_description': 'Discover the perfect All-in-One washer dryer for your Sandy Springs home. Our selection features ventless design, inverter heatpump technology, mega capacity lets you fit more in every load.',
        # 页面内容描述，显示在页面中
        # 例如：'Discover the perfect washing machine for your Atlanta home. Our selection features energy-efficient models with smart technology and large capacity.'

        'features': [
            'ventless design',           # 产品特色1
            'inverter heatpump technology',           # 产品特色2
            'mega capacity 5.0+ cu.ft. lets you fit more in every load',           # 产品特色3
            'lg and samsung all-in-one washer dryer',           # 产品特色4
            'sandy springs apartment friendly'        # 本地服务特色
        ],
        # 例如：['Energy Star certified models', 'Smart WiFi connectivity', 'Large capacity options', 'Quiet operation technology', 'Same-day delivery in Atlanta']

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/all-in-one-washer-dryer.jpg',
        # 产品特色图片路径，显示在首页卡片中
        # 建议尺寸：600x400px，例如：'/static/frontend/images/products/washing-machines.jpg'

        'background_image': '/static/frontend/images/city/Desktop-SandySprings.webp',
        # 城市背景图片路径，显示在产品页面中
        # 例如：'/static/frontend/images/city/Desktop-Atlanta.webp'

        'icon': 'washing-machine',
        # 图标标识符，用于显示SVG图标（如果没有图片时）
        # 可选值：'refrigerator', 'washing-machine', 'appliance-set', 'discount' 等
    },

    'lg-truesteam-dishwasher-norcross': {
        # === 基础SEO信息 ===
        'title': 'Best LG TrueSteam Dishwashers in Norcross GA - Appliances 4 Less',
        'meta_description': 'Shop premium LG TrueSteam dishwashers in Norcross, GA. Advanced steam cleaning technology for sparkling dishes. Same-day delivery subject to availability.',
        'h1_title': 'LG TrueSteam Dishwashers in Norcross, Georgia',
        'short_title': 'LG TrueSteam Dishwashers',

        # === 地理位置信息 ===
        'city_key': 'norcross',

        # === 首页显示设置 ===
        'show_on_homepage': True,
        'homepage_priority': 5,
        'active': True,

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,
                'order__isnull': True,
                'company_id': 'from_settings'
            },

            # 类别筛选
            'category': {
                'names': ['Dishwasher'],
            },

            # 品牌筛选
            'brand': {
                'name__iexact': 'LG',
            },

            # 产品模型筛选 - 描述包含truesteam
            'product_model': {
                'description__icontains': 'truesteam',
            },
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'lg truesteam dishwasher norcross',
            'lg dishwasher norcross ga',
            'truesteam dishwasher norcross',
            'steam cleaning dishwasher',
            'lg quadwash dishwasher norcross'
        ],

        # === 页面内容 ===
        'content_description': 'Discover the perfect LG TrueSteam dishwasher for your Norcross home. Our selection features advanced steam cleaning technology that eliminates 99.9% of bacteria for truly clean dishes.',

        'features': [
            'TrueSteam technology eliminates 99.9% of bacteria',
            'QuadWash spray arms for complete coverage',
            'Dynamic Dry for spotless results',
            'SmartThinQ app connectivity',
            'FREE delivery in Norcross area'
        ],

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/lg-truesteam-dishwasher.webp',
        'background_image': '/static/frontend/images/city/Desktop-Norcross.webp',
        'icon': 'dishwasher',
    },

    'upright-freezers-peachtree-corners': {
        'title': 'Best Upright Freezers in Peachtree Corners GA - Appliances 4 Less',
        'meta_description': 'Shop premium Upright freezers in Peachtree Corners, GA. Energy efficient models with large capacity. Same-day delivery subject to availability.',
        'h1_title': 'Upright Freezers in Peachtree Corners, Georgia',
        'short_title': 'Upright Freezers',
        'city_key': 'peachtree_corners',
        'show_on_homepage': True,
        'homepage_priority': 6,
        'active': True,
        'filters': {
            'basic': {
                'published': True,
                'order__isnull': True,
                'company_id': 'from_settings'
            },
            # 类别筛选
            'category': {
                'names': ['Freezer'],
            },
        },
        'min_inventory': 1,
        'keywords': [
            'upright freezers peachtree corners',
            'upright freezer peachtree corners ga',
            'energy efficient upright freezer',
            'large capacity upright freezer',
            'peachtree corners apartment friendly'
        ],
        'content_description': 'Discover the perfect Upright freezer for your Peachtree Corners home. Our selection features energy-efficient models with large capacity.',
        'features': [
            'energy efficient models',
            'large capacity',
            'peachtree corners apartment friendly'
        ],
        'featured_image': '/static/frontend/images/products/upright-freezers.webp',
        'background_image': '/static/frontend/images/city/Desktop-PeachtreeCorners.webp',
        'icon': 'freezer',
    },
    'lg-gas-cooktop-dunwoody':{

        # === 基础SEO信息 ===
        'title': 'Best LG Gas Cooktop in Dunwoody GA - Appliances 4 Less',
        # 页面标题，显示在浏览器标签栏和搜索结果中，建议60字符以内
        # 例如：'Best Washing Machines in Atlanta GA - Appliances 4 Less'

        'meta_description': 'Shop premium LG Gas cooktop in Dunwoody, GA. UltraHeat 20K BTU burners for fast and even cooking. Same-day delivery subject to availability.',
        # 页面描述，显示在搜索结果中，建议150-160字符以内
        # 例如：'Shop premium washing machines in Atlanta, GA. Energy efficient models with smart features. Same-day delivery available.'

        'h1_title': 'LG Gas Cooktop in Dunwoody, Georgia',
        # 页面主标题，显示在页面顶部
        # 例如：'Washing Machines in Atlanta, Georgia'

        'short_title': 'LG Gas Cooktop',
        # 简短标题，用于导航和卡片显示
        # 例如：'Washing Machines'

        # === 地理位置信息 ===
        'city_key': 'dunwoody',
        # 城市标识符，必须与CITIES配置中的key匹配
        # 例如：'atlanta', 'doraville', 'chamblee'

        # === 首页显示设置 ===
        'show_on_homepage': True,
        'homepage_priority': 7,
        'active': True,

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,              # 只显示已发布的产品
                'order__isnull': True,          # 只显示未售出的产品
                'company_id': 'from_settings'   # 自动从settings获取公司ID
            },

            # 类别筛选（可选）- 二选一使用
            # 注意：会自动包含所有子类别！例如 'Dishwasher' 会匹配所有洗碗机子类别
             'category': {
                 'names': ['Cooktop'],  # 按类别名称筛选（自动包含子类别）
                 # 或者使用slug筛选：
                 # 'slugs': ['category-slug-1', 'category-slug-2'],  # 按类别slug筛选（自动包含子类别）
            },

            # 产品模型筛选（推荐使用）
            #'product_model': {
                # 按型号筛选（推荐）- 支持逗号分隔多个型号
                #'model_number__icontains': 'MODEL1, MODEL2, MODEL3',
                # 例如：'WF45T6000AW, WF45T6200AW, WF50T8500AV'

                # 或者按描述筛选（可选）
                # 'description__icontains': 'keyword in description',
            #},

            # 库存条件筛选（可选）
            # 'inventory': {
            #     'condition__in': ['BRAND_NEW', 'OPEN_BOX'],  # 只显示特定条件的产品
            # }
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'lg gas cooktop dunwoody',      # 主关键词
            'lg gas cooktop dunwoody ga',   # 带州名的关键词
            'ultraheat 20k btu burners',        # 特定功能关键词
            'lg life is good',           # 品牌相关关键词
            'dunwoody apartment friendly'            # 本地服务关键词
        ],
        # 例如：['washing machines atlanta', 'washers atlanta ga', 'front load washers', 'samsung lg washers', 'washer delivery atlanta']

        # === 页面内容 ===
        'content_description': 'Discover the perfect LG Gas Cooktop for your Dunwoody home. Our selection features UltraHeat 20K BTU burners for fast and even cooking.',
        # 页面内容描述，显示在页面中
        # 例如：'Discover the perfect washing machine for your Atlanta home. Our selection features energy-efficient models with smart technology and large capacity.'

        'features': [
            'UltraHeat 20K BTU burner for rapid boiling and true simmering',           # 产品特色1
            'Continuous cast iron grates provide even heating and stability for your cookware',           # 产品特色2
            'Wipe away stains with ease thanks to the specially coated EasyClean surface',           # 产品特色3
            'Auto Reignition automatically reignites the burners if the flame accidentally goes out',           # 产品特色4
            'dunwoody free delivery'        # 本地服务特色
        ],
        # 例如：['Energy Star certified models', 'Smart WiFi connectivity', 'Large capacity options', 'Quiet operation technology', 'Same-day delivery in Atlanta']

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/cooktop.webp',
        # 产品特色图片路径，显示在首页卡片中
        # 建议尺寸：600x400px，例如：'/static/frontend/images/products/washing-machines.jpg'

        'background_image': '/static/frontend/images/city/Desktop-Dunwoody.webp',
        # 城市背景图片路径，显示在产品页面中
        # 例如：'/static/frontend/images/city/Desktop-Atlanta.webp'

        'icon': 'cooktop',
        # 图标标识符，用于显示SVG图标（如果没有图片时）
        # 可选值：'refrigerator', 'washing-machine', 'appliance-set', 'discount' 等
    },

    'induction-ranges-brookhaven': {
        # === 基础SEO信息 ===
        'title': 'Best Induction Ranges in Brookhaven GA - Appliances 4 Less',
        'meta_description': 'Shop premium induction ranges in Brookhaven, GA. 85% more energy efficient than electric, faster cooking, precise temperature control. Same-day delivery available.',
        'h1_title': 'Induction Ranges in Brookhaven, Georgia',
        'short_title': 'Induction Ranges',

        # === 地理位置信息 ===
        'city_key': 'brookhaven',

        # === 首页显示设置 ===
        'show_on_homepage': True,
        'homepage_priority': 8,
        'active': True,

        # === 产品筛选条件 ===
        'filters': {
            # 基础筛选（必须包含）
            'basic': {
                'published': True,              # 只显示已发布的产品
                'order__isnull': True,          # 只显示未售出的产品
                'company_id': 'from_settings'   # 自动从settings获取公司ID
            },

            # 类别筛选 - 使用 Induction Range 类别
            'category': {
                'names': ['Induction Range'],  # 按类别名称筛选（自动包含子类别）
            },
        },

        # 最少库存数量，低于此数量页面自动隐藏
        'min_inventory': 1,

        # === SEO关键词 ===
        'keywords': [
            'induction ranges brookhaven',                    # 主关键词
            'induction stove brookhaven ga',                  # 带州名的关键词
            'induction range vs electric brookhaven',         # 对比关键词
            'energy efficient induction cooktop',             # 能效关键词
            'fast cooking induction range',                   # 功能关键词
            'precise temperature control range',              # 精准温控关键词
            'safe cooktop brookhaven ga'                      # 安全特性关键词
        ],

        # === 页面内容 ===
        'content_description': 'Discover the perfect induction range for your Brookhaven home. Unlike traditional electric ranges, induction technology heats cookware directly through electromagnetic fields, delivering 85% energy efficiency, 20-40% faster cooking, and instant temperature control—all while keeping your cooktop cool to the touch.',

        'features': [
            '85% more energy efficient than traditional electric ranges',
            '20-40% faster cooking - boils water 2-4 minutes quicker',
            'Instant and precise temperature control for perfect cooking results',
            'Cooktop stays cool to touch - safer than electric coil ranges',
            'Easy cleanup - spills don\'t burn onto the cool surface',
            'FREE delivery in Brookhaven area'
        ],

        # === 页面展示素材 ===
        'featured_image': '/static/frontend/images/products/induction-range.webp',
        # 产品特色图片路径，显示在首页卡片中
        # 建议尺寸：600x400px

        'background_image': '/static/frontend/images/city/Desktop-Brookhaven.webp',
        # 城市背景图片路径，显示在产品页面中

        'icon': 'range',
        # 图标标识符，用于显示SVG图标（如果没有图片时）
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

def get_category_with_descendants(category):
    """
    递归获取类别及其所有子孙类别的ID列表

    Args:
        category: Category对象

    Returns:
        list: 包含该类别及所有子孙类别的ID列表
    """
    category_ids = [category.id]

    # 递归获取所有子类别
    for subcategory in category.subcategories.all():
        category_ids.extend(get_category_with_descendants(subcategory))

    return category_ids


def build_product_filters(config):
    """
    根据配置构建Django QuerySet过滤条件

    支持新的filters结构：
    {
        'basic': {'published': True, 'company_id': 'from_settings'},
        'category': {'names': [...], 'slugs': [...]},  # 自动包含所有子类别
        'brand': {'name__iexact': 'LG', 'slug__iexact': 'lg'},
        'product_model': {'description__icontains': '...', 'model_numbers': [...]},
        'inventory': {'condition__in': [...]}
    }

    注意：
    - category筛选会自动递归包含所有子类别
      例如：'Dishwasher' 会同时匹配 'Dishwasher' 及其所有子类别（如 'Built-in Dishwasher', 'Portable Dishwasher' 等）

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

    # 类别筛选（自动包含子类别）
    if 'category' in filter_config:
        from frontend.models_proxy import Category
        category_config = filter_config['category']
        category_ids = []

        # 通过类别名称筛选
        if 'names' in category_config:
            # 获取所有匹配的父类别
            parent_categories = Category.objects.filter(name__in=category_config['names'])

            # 递归获取每个父类别及其所有子孙类别
            for parent in parent_categories:
                category_ids.extend(get_category_with_descendants(parent))

        # 通过类别slug筛选
        elif 'slugs' in category_config:
            # 获取所有匹配的父类别
            parent_categories = Category.objects.filter(slug__in=category_config['slugs'])

            # 递归获取每个父类别及其所有子孙类别
            for parent in parent_categories:
                category_ids.extend(get_category_with_descendants(parent))

        # 使用ID列表进行筛选（包含父类别和所有子类别）
        if category_ids:
            filters &= Q(model_number__category_id__in=category_ids)

    # 品牌筛选
    if 'brand' in filter_config:
        brand_config = filter_config['brand']
        for field, value in brand_config.items():
            filters &= Q(**{f'model_number__brand__{field}': value})

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

# ==================== 使用说明 ====================
"""
如何添加新的SEO页面：

1. 复制 PRODUCT_SEO_PAGE_TEMPLATE 中的模板内容
2. 粘贴到 PRODUCT_SEO_PAGES 字典中
3. 修改页面标识符（key）为实际的产品-城市组合
4. 根据注释修改各个字段的内容
5. 准备相应的产品图片放到 /static/frontend/images/products/ 目录
6. 确保城市背景图片存在于 /static/frontend/images/city/ 目录

示例添加洗衣机页面：

'washing-machines-atlanta': {
    'title': 'Best Washing Machines in Atlanta GA - Appliances 4 Less',
    'meta_description': 'Shop premium washing machines in Atlanta, GA. Energy efficient front load and top load models. Same-day delivery available.',
    'h1_title': 'Washing Machines in Atlanta, Georgia',
    'short_title': 'Washing Machines',
    'city_key': 'atlanta',
    'show_on_homepage': True,
    'homepage_priority': 3,
    'active': True,
    'filters': {
        'basic': {
            'published': True,
            'order__isnull': True,
            'company_id': 'from_settings'
        },
        'product_model': {
            'model_number__icontains': 'WF45T6000AW, WF45T6200AW, WF50T8500AV',
        }
    },
    'min_inventory': 1,
    'keywords': [
        'washing machines atlanta',
        'washers atlanta ga',
        'front load washing machines',
        'energy star washers',
        'washer delivery atlanta'
    ],
    'content_description': 'Discover the perfect washing machine for your Atlanta home. Our selection features energy-efficient models with smart technology and large capacity.',
    'features': [
        'Energy Star certified models',
        'Smart WiFi connectivity available',
        'Large capacity options',
        'Quiet operation technology',
        'Same-day delivery in Atlanta area'
    ],
    'featured_image': '/static/frontend/images/products/washing-machines.jpg',
    'background_image': '/static/frontend/images/city/Desktop-Atlanta.webp',
    'icon': 'washing-machine',
},

注意事项：
- 页面标识符必须唯一且使用小写字母和连字符
- city_key 必须在 CITIES 配置中存在
- 产品型号需要存在于数据库中
- 图片文件需要实际存在于指定路径
- 建议先设置 active: False 测试，确认无误后再激活
"""