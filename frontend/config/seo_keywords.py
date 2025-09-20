"""
SEO关键词配置文件
管理城市和服务相关的长尾关键词，避免硬编码
"""

# 服务类型配置
SERVICE_TYPES = {
    'appliance_delivery': {
        'name': 'Delivery',
        'keywords': ['delivery', 'appliance delivery', 'home delivery'],
        'description': 'Professional appliance delivery service with careful handling. Drop off your appliances at your garage or driveway. Free within 10 miles. 10-20 miles $50 delivery fee. 20-30 miles $75 delivery fee. 30-40 miles $100 delivery fee.',
        'price_range': '$0-$100',
        'duration': '0.5-2 hours',
        'features': ['Same-day delivery (subject to availability)', 'Careful handling', 'Free within 10 miles', 'Professional team'],
        'image_desktop': '/static/frontend/images/services/Desktop-delivery.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-delivery.jpg',
        'icon': 'truck',
        'category': 'logistics'
    },
    'refrigerator_installation': {
        'name': 'Refrigerator Installation',
        'keywords': ['Refrigerator Installation', 'fridge setup', 'appliance installation'],
        'description': 'Expert refrigerator installation including, move your refrigerator to kitchen, water line connection, and leveling',
        'price_range': '$20',
        'duration': '0.5-1.5 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-refrigerator.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-refrigerator.jpg',
        'icon': 'refrigerator',
        'category': 'installation'
    },
    'washer_installation': {
        'name': 'Washer Installation',
        'keywords': ['Washer Installation', 'washing machine setup', 'laundry appliance'],
        'description': 'Complete washer installation with water and electrical connections, move your washer to laundry room',
        'price_range': '$25',
        'duration': '0.5-1 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-washer.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-washer.jpg',
        'icon': 'washing-machine',
        'category': 'installation'
    },
    'dryer_installation': {
        'name': 'Dryer Installation',
        'keywords': ['Dryer Installation', 'clothes dryer setup', 'laundry appliance'],
        'description': 'Professional dryer installation with venting and electrical connections, move your dryer to laundry room',
        'price_range': '$35',
        'duration': '0.5-1 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-dryer.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-dryer.jpg',
        'icon': 'dryer',
        'category': 'installation'
    },
    'electric_stove_installation': {
        'name': 'Electric Stove Installation',
        'keywords': ['Electric Stove Installation', 'range setup', 'cooking appliance'],
        'description': 'Safe stove installation with electrical connections, move your stove to kitchen',
        'price_range': '$30',
        'duration': '0.5-1 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-stove.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-stove.jpg',
        'icon': 'stove',
        'category': 'installation'
    },
    'dishwasher_installation': {
        'name': 'Dishwasher Installation',
        'keywords': ['Dishwasher Installation', 'dishwasher setup', 'kitchen appliance'],
        'description': 'Complete dishwasher installation with plumbing and electrical connections, move your dishwasher to kitchen',
        'price_range': '$120',
        'duration': '1-2 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-dishwasher.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-dishwasher.jpg',
        'icon': 'dishwasher',
        'category': 'installation'
    },
    'microwave_installation': {
        'name': 'Microwave Installation',
        'keywords': ['Microwave Installation', 'microwave setup', 'kitchen appliance'],
        'description': 'Microwave installation including mounting and electrical connections, move your microwave to kitchen',
        'price_range': '$120',
        'duration': '1-2 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-microwave.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-microwave.jpg',
        'icon': 'microwave',
        'category': 'installation'
    },
    'wall_oven_installation': {
        'name': 'Wall Oven Installation',
        'keywords': ['Wall Oven Installation', 'oven setup', 'cooking appliance'],
        'description': 'Professional wall oven installation with electrical connections, move your wall oven to kitchen',
        'price_range': '$250',
        'duration': '1-2 hours',
        'features': ['Same-day service (subject to availability)', 'Experienced technicians', '1-year warranty', 'Accessories included'],
        'image_desktop': '/static/frontend/images/services/Desktop-wall-oven.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-wall-oven.jpg',
        'icon': 'oven',
        'category': 'installation'
    },
    'appliances_haul_away': {
        'name': 'Appliances Haul Away',
        'keywords': ['Appliances Haul Away', 'appliance removal', 'old appliance disposal'],
        'description': 'Professional removal and disposal of old appliances, move your appliances to your garage or driveway',
        'price_range': '$30',
        'duration': '0.5-1 hours',
        'features': ['Same-day pickup (subject to availability)', 'Eco-friendly disposal'],
        'image_desktop': '/static/frontend/images/services/Desktop-haul-away.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-haul-away.jpg',
        'icon': 'trash',
        'category': 'disposal'
    },
    'appliance_recycle': {
        'name': 'Recycle',
        'keywords': ['Recycle', 'appliance recycling', 'eco-friendly disposal'],
        'description': 'Environmentally responsible appliance recycling service, move your appliances to recycling center',
        'price_range': 'Free',
        'duration': '0.5-1 hours',
        'features': ['Eco-friendly', 'Free pickup (subject to availability)', 'Certified recycling'],
        'image_desktop': '/static/frontend/images/services/Desktop-recycle.jpg',
        'image_mobile': '/static/frontend/images/services/Mobile-recycle.jpg',
        'icon': 'recycle',
        'category': 'disposal'
    }
}

# 城市配置
CITIES = {
    'doraville': {
        'name': 'Doraville',
        'state': 'GA',
        'full_name': 'Doraville, GA',
        'nearby_cities': ['Chamblee', 'Norcross', 'Tucker', 'Brookhaven'],
        'description': 'A vibrant city in DeKalb County, Georgia, known for its diverse community and convenient location near Atlanta',
        'population': '10,000+',
        'area': '2.5 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Doraville.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Doraville.webp',
        'highlights': ['Diverse community', 'Convenient location', 'Growing business district', 'Family-friendly']
    },
    'chamblee': {
        'name': 'Chamblee',
        'state': 'GA', 
        'full_name': 'Chamblee, GA',
        'nearby_cities': ['Doraville', 'Brookhaven', 'Norcross'],
        'description': 'A historic city in DeKalb County with a rich railroad heritage and growing commercial district',
        'population': '30,000+',
        'area': '8.2 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Chamblee.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Chamblee.webp',
        'highlights': ['Historic downtown', 'Railroad heritage', 'Commercial growth', 'Community events']
    },
    'norcross': {
        'name': 'Norcross',
        'state': 'GA',
        'full_name': 'Norcross, GA', 
        'nearby_cities': ['Duluth', 'Tucker', 'Peachtree Corners','Lilburn','Doraville'],
        'description': 'A charming historic city in Gwinnett County known for its preserved downtown and community spirit',
        'population': '17,000+',
        'area': '4.3 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Norcross.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Norcross.webp',
        'highlights': ['Historic downtown', 'Community spirit', 'Cultural events', 'Small-town charm']
    },
    'duluth': {
        'name': 'Duluth',
        'state': 'GA',
        'full_name': 'Duluth, GA',
        'nearby_cities': ['Norcross', 'Peachtree Corners'],
        'description': 'A thriving city in Gwinnett County with excellent schools, parks, and a strong business community',
        'population': '30,000+',
        'area': '10.1 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Duluth.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Duluth.webp',
        'highlights': ['Excellent schools', 'Beautiful parks', 'Strong business community', 'Family-oriented']
    },
    'tucker': {
        'name': 'Tucker',
        'state': 'GA',
        'full_name': 'Tucker, GA',
        'nearby_cities': ['Doraville', 'Norcross', 'Lilburn'],
        'description': 'A growing community in DeKalb County with a mix of residential and commercial development',
        'population': '37,000+',
        'area': '8.7 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Tucker.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Tucker.webp',
        'highlights': ['Growing community', 'Mixed development', 'Community events', 'Accessible location']
    },
    'brookhaven': {
        'name': 'Brookhaven',
        'state': 'GA',
        'full_name': 'Brookhaven, GA',
        'nearby_cities': ['Chamblee', 'Atlanta', 'Sandy Springs'],
        'description': 'A vibrant city in DeKalb County known for its parks, shopping, and proximity to Atlanta',
        'population': '55,000+',
        'area': '7.0 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Brookhaven.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Brookhaven.webp',
        'highlights': ['Beautiful parks', 'Shopping district', 'Proximity to Atlanta', 'Active community']
    },
    'lilburn': {
        'name': 'Lilburn',
        'state': 'GA',
        'full_name': 'Lilburn, GA',
        'nearby_cities': ['Tucker', 'Norcross'],
        'description': 'A diverse city in Gwinnett County with a strong sense of community and cultural diversity',
        'population': '13,000+',
        'area': '6.4 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Lilburn.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Lilburn.webp',
        'highlights': ['Cultural diversity', 'Community spirit', 'Historic downtown', 'Family-friendly']
    },
    'sandy_springs': {
        'name': 'Sandy Springs',
        'state': 'GA',
        'full_name': 'Sandy Springs, GA',
        'nearby_cities': ['Brookhaven', 'Norcross','Doraville','Brookhaven','Chamblee'],
        'description': 'A thriving city in Fulton County known for its business district, parks, and quality of life',
        'population': '110,000+',
        'area': '37.7 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-SandySprings.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-SandySprings.webp',
        'highlights': ['Business district', 'Beautiful parks', 'High quality of life', 'Cultural attractions']
    },
    'dunwoody': {
        'name': 'Dunwoody',
        'state': 'GA',
        'full_name': 'Dunwoody, GA',
        'nearby_cities': ['Sandy Springs', 'Brookhaven', 'Chamblee','Doraville','Lilburn'],
        'description': 'An affluent city in DeKalb County known for its excellent schools and business community',
        'population': '50,000+',
        'area': '12.0 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-Dunwoody.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-Dunwoody.webp',
        'highlights': ['Excellent schools', 'Business community', 'Affluent area', 'Community events']
    },
    'peachtree_corners': {
        'name': 'Peachtree Corners',
        'state': 'GA',
        'full_name': 'Peachtree Corners, GA',
        'nearby_cities': ['Duluth', 'Norcross','Lilburn','Tucker','Doraville'],
        'description': 'A modern city in Gwinnett County, known for its technology companies, excellent schools, and family-friendly community',
        'population': '45,000+',
        'area': '16.2 sq mi',
        'image_desktop': '/static/frontend/images/city/Desktop-PeachtreeCorners.webp',
        'image_mobile': '/static/frontend/images/city/Mobile-PeachtreeCorners.webp',
        'highlights': ['Technology hub', 'Family-friendly', 'Excellent schools', 'Modern community']
    }
}

# 长尾关键词模板
KEYWORD_TEMPLATES = {
    'city_service': '{city_name}{service_name}Service', 
    'city_appliance_service': '{city_name}Appliance{service_name}',
    'city_delivery_installation': '{city_name}Appliance Delivery installation One-Stop Service',
    'city_recycle_service': '{city_name}Appliance Recycle Service',
    'nearby_city_service': '{city_name}Nearby Appliance{service_name}Service',
    'metro_area_service': 'Atlanta Area Appliance{service_name}'
}

def generate_keywords(city_key, service_key):
    """
    根据城市和服务类型生成长尾关键词
    
    Args:
        city_key: 城市键名
        service_key: 服务类型键名
    
    Returns:
        list: 生成的关键词列表
    """
    if city_key not in CITIES or service_key not in SERVICE_TYPES:
        return []
    
    city = CITIES[city_key]
    service = SERVICE_TYPES[service_key]
    keywords = []
    
    # 生成各种模板的关键词
    templates = [
        f"{city['name']}{service['name']}Service",
        f"{city['name']}Appliance{service['name']}",
        f"{city['name']}Appliance Delivery installation One-Stop Service",
        f"{city['name']}Appliance Recycle Service",
        f"{city['name']}Nearby Appliance{service['name']}Service"
    ]
    
    # 如果是主要城市，添加大区域关键词
    if city_key in ['atlanta', 'doraville']:
        templates.append(f"Atlanta Area Appliance{service['name']}")
    
    return templates

def get_all_city_service_combinations():
    """
    获取所有城市和服务类型的组合关键词
    
    Returns:
        dict: 城市-服务组合的关键词字典
    """
    combinations = {}
    
    for city_key in CITIES.keys():
        combinations[city_key] = {}
        for service_key in SERVICE_TYPES.keys():
            combinations[city_key][service_key] = generate_keywords(city_key, service_key)
    
    return combinations

def get_city_by_slug(slug):
    """
    根据slug获取城市信息
    
    Args:
        slug: 城市slug
    
    Returns:
        dict: 城市信息字典，如果不存在返回None
    """
    return CITIES.get(slug)

def get_service_by_key(key):
    """
    根据key获取服务信息
    
    Args:
        key: 服务key
    
    Returns:
        dict: 服务信息字典，如果不存在返回None
    """
    return SERVICE_TYPES.get(key)

def get_nearby_cities(city_key):
    """
    获取指定城市的附近城市列表
    
    Args:
        city_key: 城市键名
    
    Returns:
        list: 附近城市列表
    """
    city = CITIES.get(city_key)
    return city['nearby_cities'] if city else []
