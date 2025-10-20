"""
结构化数据辅助函数
与 nasmaha 项目的 google_merchant_service.py 保持完全一致
确保 Schema.org 结构化数据和 Google Merchant Content API 数据一致
"""
from django.templatetags.static import static


def get_structured_data_title(item):
    """
    生成结构化数据标题（与 google_merchant_service._get_title 一致）

    格式: Brand Model - Category (Condition)
    例如: "Samsung RF23M8070SR - Refrigerator (Open Box)"

    Args:
        item: InventoryItem对象

    Returns:
        str: 产品标题（最多150字符）
    """
    brand = item.model_number.brand.name
    model = item.model_number.model_number
    category = item.model_number.category.name
    condition = item.get_condition_display()

    # 格式: Brand Model - Category (Condition)
    title = f"{brand} {model} - {category} ({condition})"

    # Google限制150字符
    if len(title) > 150:
        title = title[:147] + "..."

    return title


def get_structured_data_description(item):
    """
    生成结构化数据描述（与 google_merchant_service._get_description 一致）

    包含3部分:
    1. 产品型号通用描述（产品特性）
    2. 单个商品的特殊描述（特殊说明，如外观瑕疵等）
    3. 保修信息

    Args:
        item: InventoryItem对象

    Returns:
        str: 产品描述
    """
    description_parts = []

    # 1. 产品型号通用描述（产品特性）
    if item.model_number.description:
        # 去除HTML标签
        import re
        clean_desc = re.sub('<[^<]+?>', '', item.model_number.description)
        description_parts.append(clean_desc)
    else:
        # 如果没有型号描述，生成默认描述
        brand = item.model_number.brand.name
        model = item.model_number.model_number
        category = item.model_number.category.name
        condition = item.get_condition_display()
        description_parts.append(f"{brand} {model} {category}. Condition: {condition}.")

    # 2. 单个商品的特殊描述（特殊说明，如外观瑕疵等）
    if item.item_description:
        description_parts.append(item.item_description)

    # 3. 保修信息
    if item.warranty_type and item.warranty_type != 'NONE':
        warranty_type = item.get_warranty_type_display()
        # 使用已计算好的 warranty_display（在视图中已设置）
        if hasattr(item, 'warranty_display'):
            warranty_period = item.warranty_display
        else:
            warranty_period = item.get_warranty_period_display()
        description_parts.append(f"Warranty: {warranty_type} - {warranty_period}.")

    # 合并所有部分，用空格分隔
    description = " ".join(description_parts)

    return description


def get_structured_data_condition(item):
    """
    获取结构化数据条件（与 google_merchant_service._get_condition 一致）

    将内部条件代码映射到 Schema.org 标准 URL

    Args:
        item: InventoryItem对象

    Returns:
        str: Schema.org condition URL
    """
    condition_mapping = {
        'BRAND_NEW': 'https://schema.org/NewCondition',
        'OPEN_BOX': 'https://schema.org/NewCondition',
        'SCRATCH_DENT': 'https://schema.org/NewCondition',
        'USED_GOOD': 'https://schema.org/UsedCondition',
        'USED_FAIR': 'https://schema.org/UsedCondition',
    }
    return condition_mapping.get(item.condition, 'https://schema.org/UsedCondition')


def get_structured_data_availability(item):
    """
    获取结构化数据可用性（与 google_merchant_service._get_availability 一致）

    根据库存状态动态判断可用性

    Args:
        item: InventoryItem对象

    Returns:
        str: Schema.org availability URL
    """
    # 状态ID说明:
    # 4: Ready for sale (可售)
    # 5: In storage (在库存中)
    # 8: Online display (在线展示)

    # 已被订单关联，不可售
    if item.order:
        return 'https://schema.org/OutOfStock'

    # 可售状态
    if item.current_state_id in [4, 5, 8]:
        return 'https://schema.org/InStock'

    return 'https://schema.org/OutOfStock'


def get_structured_data_images(item, request):
    """
    获取结构化数据图片列表（与 google_merchant_service 逻辑一致）

    优先使用 ItemImage（实物图），如果没有则使用 ProductModel 图片

    Args:
        item: InventoryItem对象
        request: HttpRequest对象

    Returns:
        list: 图片绝对URL列表
    """
    base_url = f"{request.scheme}://{request.get_host()}"
    images = []

    # 1. 优先使用 ItemImage（实物拍摄图片）
    item_images = item.images.all()
    if item_images.exists():
        for image in item_images:
            images.append(f"{base_url}{image.image.url}")

    # 2. 如果没有 ItemImage，使用 ProductModel 图片作为备用
    if not images:
        model_images = item.model_number.images.all()
        if model_images.exists():
            for image in model_images:
                images.append(f"{base_url}{image.image.url}")

    # 3. 如果都没有图片，返回默认图片
    if not images:
        default_image = static('frontend/images/product-default.png')
        images.append(f"{base_url}{default_image}")

    return images


def get_all_structured_data(item, request):
    """
    获取所有结构化数据字段的便捷函数

    Args:
        item: InventoryItem对象
        request: HttpRequest对象

    Returns:
        dict: 包含所有结构化数据字段的字典
    """
    return {
        'structured_title': get_structured_data_title(item),
        'structured_description': get_structured_data_description(item),
        'structured_condition': get_structured_data_condition(item),
        'structured_availability': get_structured_data_availability(item),
        'structured_images': get_structured_data_images(item, request),
    }
