from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def transaction_type_badge(transaction_type):
    """
    生成交易类型的颜色标签
    """
    type_colors = {
        'DEPOSIT': 'bg-green-100 text-green-800',
        'WITHDRAWAL': 'bg-red-100 text-red-800',
        'CONSUMPTION': 'bg-orange-100 text-orange-800',
        'CANCELLATION': 'bg-purple-100 text-purple-800',
        'VIRTUAL_DEPOSIT': 'bg-emerald-100 text-emerald-800',
        'VIRTUAL_WITHDRAWAL': 'bg-rose-100 text-rose-800',
    }
    
    color_class = type_colors.get(transaction_type, 'bg-gray-100 text-gray-800')
    
    # 获取交易类型显示名称
    type_display = {
        'DEPOSIT': 'Deposit',
        'WITHDRAWAL': 'Withdrawal',
        'CONSUMPTION': 'Consumption',
        'CANCELLATION': 'Cancellation',
        'VIRTUAL_DEPOSIT': 'Virtual Deposit',
        'VIRTUAL_WITHDRAWAL': 'Virtual Withdrawal',
    }
    
    display_name = type_display.get(transaction_type, transaction_type)
    
    html = f'<span class="px-3 py-1 {color_class} rounded-full text-sm font-medium">{display_name}</span>'
    return mark_safe(html)

@register.simple_tag
def transaction_type_color_class(transaction_type):
    """
    只返回交易类型的颜色类名，不包含HTML
    """
    type_colors = {
        'DEPOSIT': 'bg-green-100 text-green-800',
        'WITHDRAWAL': 'bg-red-100 text-red-800',
        'CONSUMPTION': 'bg-orange-100 text-orange-800',
        'CANCELLATION': 'bg-purple-100 text-purple-800',
        'VIRTUAL_DEPOSIT': 'bg-emerald-100 text-emerald-800',
        'VIRTUAL_WITHDRAWAL': 'bg-rose-100 text-rose-800',
    }
    
    return type_colors.get(transaction_type, 'bg-gray-100 text-gray-800')

@register.simple_tag
def payment_method_badge(payment_method):
    """
    生成支付方式的颜色标签
    """
    method_colors = {
        'CREDIT_CARD': 'bg-blue-100 text-blue-800',
        'DEBIT_CARD': 'bg-indigo-100 text-indigo-800',
        'CASH': 'bg-green-100 text-green-800',
        'ZELLE': 'bg-purple-100 text-purple-800',
        'BANK_TRANSFER': 'bg-cyan-100 text-cyan-800',
        'SNAP_FINANCE': 'bg-yellow-100 text-yellow-800',
        'SNAP_CREDIT': 'bg-amber-100 text-amber-800',
        'ACIMA_FINANCE': 'bg-orange-100 text-orange-800',
        'AMERICAN_FIRST_FINANCE': 'bg-red-100 text-red-800',
        'CHECK': 'bg-gray-100 text-gray-800',
        'OTHER': 'bg-slate-100 text-slate-800',
    }
    
    color_class = method_colors.get(payment_method, 'bg-gray-100 text-gray-800')
    
    # 获取支付方式显示名称
    method_display = {
        'CREDIT_CARD': 'Credit Card',
        'DEBIT_CARD': 'Debit Card',
        'CASH': 'Cash',
        'ZELLE': 'Zelle',
        'BANK_TRANSFER': 'Bank Transfer',
        'SNAP_FINANCE': 'Snap Finance',
        'SNAP_CREDIT': 'Snap Credit',
        'ACIMA_FINANCE': 'Acima Finance',
        'AMERICAN_FIRST_FINANCE': 'American First Finance',
        'CHECK': 'Check',
        'OTHER': 'Other',
    }
    
    display_name = method_display.get(payment_method, payment_method)
    
    html = f'<span class="px-3 py-1 {color_class} rounded-full text-sm font-medium">{display_name}</span>'
    return mark_safe(html)

@register.simple_tag
def payment_method_color_class(payment_method):
    """
    只返回支付方式的颜色类名，不包含HTML
    """
    method_colors = {
        'CREDIT_CARD': 'bg-blue-100 text-blue-800',
        'DEBIT_CARD': 'bg-indigo-100 text-indigo-800',
        'CASH': 'bg-green-100 text-green-800',
        'ZELLE': 'bg-purple-100 text-purple-800',
        'BANK_TRANSFER': 'bg-cyan-100 text-cyan-800',
        'SNAP_FINANCE': 'bg-yellow-100 text-yellow-800',
        'SNAP_CREDIT': 'bg-amber-100 text-amber-800',
        'ACIMA_FINANCE': 'bg-orange-100 text-orange-800',
        'AMERICAN_FIRST_FINANCE': 'bg-red-100 text-red-800',
        'CHECK': 'bg-gray-100 text-gray-800',
        'OTHER': 'bg-slate-100 text-slate-800',
    }
    
    return method_colors.get(payment_method, 'bg-gray-100 text-gray-800')

@register.simple_tag
def transaction_amount_display(amount, transaction_type):
    """
    根据交易类型和金额生成带颜色的金额显示
    """
    # 确定颜色
    if transaction_type in ['DEPOSIT', 'VIRTUAL_DEPOSIT', 'CANCELLATION']:
        # 正数交易（存款、虚拟存款、退款）
        color_class = 'text-green-600 font-semibold'
        prefix = '+'
    elif transaction_type in ['WITHDRAWAL', 'VIRTUAL_WITHDRAWAL', 'CONSUMPTION']:
        # 负数交易（取款、虚拟取款、消费）
        color_class = 'text-red-600 font-semibold'
        prefix = ''
    else:
        color_class = 'text-gray-600 font-semibold'
        prefix = ''
    
    # 格式化金额
    formatted_amount = f"${abs(amount):.2f}"
    
    html = f'<span class="{color_class}">{prefix}{formatted_amount}</span>'
    return mark_safe(html) 