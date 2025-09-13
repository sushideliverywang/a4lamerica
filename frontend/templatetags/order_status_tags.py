from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def order_status_badge(order_status):
    """
    生成订单状态的颜色标签
    """
    status_colors = {
        'PENDING': 'bg-yellow-100 text-yellow-800',
        'CONFIRMED': 'bg-blue-100 text-blue-800',
        'UPDATED': 'bg-indigo-100 text-indigo-800',
        'SCHEDULED': 'bg-purple-100 text-purple-800',
        'PICKED_UP': 'bg-orange-100 text-orange-800',
        'SHIPPED': 'bg-cyan-100 text-cyan-800',
        'DELIVERED': 'bg-green-100 text-green-800',
        'CANCELLED': 'bg-red-100 text-red-800',
        'REFUNDED': 'bg-gray-100 text-gray-800',
    }
    
    color_class = status_colors.get(order_status, 'bg-gray-100 text-gray-800')
    
    # 获取状态显示名称
    status_display = {
        'PENDING': 'Pending',
        'CONFIRMED': 'Confirmed',
        'UPDATED': 'Updated',
        'SCHEDULED': 'Scheduled',
        'PICKED_UP': 'Picked Up',
        'SHIPPED': 'Shipped',
        'DELIVERED': 'Delivered',
        'CANCELLED': 'Cancelled',
        'REFUNDED': 'Refunded',
    }
    
    display_name = status_display.get(order_status, order_status)
    
    html = f'<span class="px-3 py-1 {color_class} rounded-full text-sm font-medium">{display_name}</span>'
    return mark_safe(html)

@register.simple_tag
def payment_status_badge(payment_status):
    """
    生成付款状态的颜色标签
    """
    status_colors = {
        'NOT_PAID': 'bg-red-100 text-red-800',
        'PAID': 'bg-green-100 text-green-800',
        'PARTIALLY_PAID': 'bg-orange-100 text-orange-800',
        'REFUNDED': 'bg-gray-100 text-gray-800',
    }
    
    color_class = status_colors.get(payment_status, 'bg-gray-100 text-gray-800')
    
    # 获取状态显示名称
    status_display = {
        'NOT_PAID': 'Not Paid',
        'PAID': 'Paid',
        'PARTIALLY_PAID': 'Partially Paid',
        'REFUNDED': 'Refunded',
    }
    
    display_name = status_display.get(payment_status, payment_status)
    
    html = f'<span class="px-3 py-1 {color_class} rounded-full text-sm font-medium">{display_name}</span>'
    return mark_safe(html)

@register.simple_tag
def order_status_color_class(order_status):
    """
    只返回订单状态的颜色类名不包含HTML
    """
    status_colors = {
        'PENDING': 'bg-yellow-100 text-yellow-800',
        'CONFIRMED': 'bg-blue-100 text-blue-800',
        'UPDATED': 'bg-indigo-100 text-indigo-800',
        'SCHEDULED': 'bg-purple-100 text-purple-800',
        'PICKED_UP': 'bg-orange-100 text-orange-800',
        'SHIPPED': 'bg-cyan-100 text-cyan-800',
        'DELIVERED': 'bg-green-100 text-green-800',
        'CANCELLED': 'bg-red-100 text-red-800',
        'REFUNDED': 'bg-gray-100 text-gray-800',
    }
    
    return status_colors.get(order_status, 'bg-gray-100 text-gray-800')

@register.simple_tag
def payment_status_color_class(payment_status):
    """
    只返回付款状态的颜色类名不包含HTML
    """
    status_colors = {
        'NOT_PAID': 'bg-red-100 text-red-800',
        'PAID': 'bg-green-100 text-green-800',
        'PARTIALLY_PAID': 'bg-orange-100 text-orange-800',
        'REFUNDED': 'bg-gray-100 text-gray-800',
    }
    
    return status_colors.get(payment_status, 'bg-gray-100 text-gray-800') 