from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter(name='vnd')
def vnd(value):
    """
    Format số tiền theo kiểu Việt Nam với dấu chấm phân cách hàng nghìn.
    Ví dụ: 30000 → 30.000đ, 1600000 → 1.600.000đ
    """
    if value is None or value == '':
        return '0đ'
    try:
        # Chuyển sang int để bỏ phần thập phân nếu có
        num = int(Decimal(str(value)))
    except (ValueError, TypeError, InvalidOperation):
        return '0đ'

    # Format với dấu chấm phân cách hàng nghìn
    formatted = '{:,}'.format(abs(num)).replace(',', '.')
    if num < 0:
        return f'-{formatted}đ'
    return f'{formatted}đ'
