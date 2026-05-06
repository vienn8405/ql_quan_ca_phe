"""
Email Service — Gửi mail thông báo cho khách hàng qua Mailtrap SMTP.

Hỗ trợ 4 luồng:
  1. Xác nhận đặt bàn (reservation confirmation)
  2. Cập nhật trạng thái đặt bàn (reservation status update)
  3. Xác nhận đơn hàng (order confirmation)
  4. Cập nhật trạng thái đơn hàng (order status update)
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


# ==================== HELPER ====================

# Map status code → display name (tiếng Việt)
RESERVATION_STATUS_MAP = {
    'pending': 'Chờ duyệt',
    'confirmed': 'Đã xác nhận',
    'seated': 'Khách đã nhận bàn',
    'completed': 'Đã hoàn thành',
    'cancelled': 'Đã hủy',
    'expired': 'Hết hạn giữ bàn',
}

ORDER_STATUS_MAP = {
    'pending': 'Chờ xử lý',
    'confirmed': 'Đã xác nhận',
    'preparing': 'Đang pha chế',
    'delivering': 'Đang giao',
    'completed': 'Hoàn tất',
    'cancelled': 'Đã hủy',
}

ORDER_TYPE_MAP = {
    'dine_in': 'Tại quán',
    'takeaway': 'Mang đi',
    'delivery': 'Giao hàng',
}

PAYMENT_MAP = {
    'cash': 'Tiền mặt',
    'stripe': 'Stripe',
}

# Màu badge theo trạng thái
STATUS_COLORS = {
    'pending': '#ffc107',
    'confirmed': '#17a2b8',
    'preparing': '#6f42c1',
    'delivering': '#fd7e14',
    'completed': '#28a745',
    'cancelled': '#dc3545',
}

# Thông điệp theo trạng thái đơn hàng
ORDER_STATUS_MESSAGES = {
    'confirmed': 'Đơn hàng của bạn đã được xác nhận và đang chờ pha chế. Cảm ơn bạn đã tin tưởng!',
    'preparing': 'Đơn hàng của bạn đang được pha chế. Vui lòng chờ trong giây lát!',
    'delivering': 'Đơn hàng của bạn đang trên đường giao đến bạn. Shipper sẽ liên hệ sớm!',
    'completed': 'Đơn hàng đã hoàn tất. Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi! ☕',
    'cancelled': 'Đơn hàng đã bị hủy. Nếu có thắc mắc, vui lòng liên hệ hotline.',
}

# Thông điệp theo trạng thái đặt bàn
RESERVATION_STATUS_MESSAGES = {
    'confirmed': 'Đặt bàn của bạn đã được xác nhận! Chúng tôi đang chờ đón bạn.',
    'seated': 'Quán đã ghi nhận bạn đã tới và nhận bàn. Chúc bạn có trải nghiệm thật vui vẻ!',
    'completed': 'Cảm ơn bạn đã đến! Hy vọng bạn có trải nghiệm tuyệt vời tại quán.',
    'cancelled': 'Đặt bàn đã bị hủy. Nếu có thắc mắc, vui lòng liên hệ hotline.',
    'expired': 'Đặt bàn đã hết hạn giữ chỗ vì quá thời gian giữ bàn. Bạn có thể tạo đặt bàn mới nếu cần.',
}


def _get_safe_branch_name(obj):
    """Lấy tên chi nhánh an toàn, tránh lỗi nếu branch bị null."""
    try:
        return obj.branch.name if obj.branch else 'Chưa xác định'
    except Exception:
        return 'Chưa xác định'


# ==================== RESERVATION ====================

def send_reservation_confirmation_email(reservation):
    """
    Gửi email xác nhận đặt bàn cho khách.

    Args:
        reservation: instance Reservation vừa tạo.
    """
    if not reservation.customer_email:
        logger.warning(
            'Bỏ qua gửi mail xác nhận đặt bàn #%s: không có email khách.',
            reservation.id,
        )
        return False

    try:
        subject = f'☕ Xác nhận đặt bàn #{reservation.id} — CafeManager'

        context = {
            'reservation': reservation,
            'branch_name': _get_safe_branch_name(reservation),
            'status_display': RESERVATION_STATUS_MAP.get(reservation.status, reservation.status),
        }

        html_content = render_to_string(
            'cafe/emails/reservation_confirmation.html', context
        )

        # Plain text fallback
        text_content = (
            f'Xác nhận đặt bàn #{reservation.id}\n'
            f'Khách: {reservation.customer_name}\n'
            f'SĐT: {reservation.customer_phone}\n'
            f'Chi nhánh: {_get_safe_branch_name(reservation)}\n'
            f'Ngày: {reservation.date}\n'
            f'Giờ: {reservation.time}\n'
            f'Số người: {reservation.guests}\n'
            f'Trạng thái: {RESERVATION_STATUS_MAP.get(reservation.status, reservation.status)}\n'
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[reservation.customer_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            'Đã gửi mail xác nhận đặt bàn #%s đến %s',
            reservation.id, reservation.customer_email,
        )
        return True

    except Exception as e:
        logger.error(
            'Lỗi gửi mail xác nhận đặt bàn #%s: %s',
            reservation.id, str(e),
        )
        return False


def send_reservation_status_update_email(reservation, old_status=None):
    """
    Gửi email cập nhật trạng thái đặt bàn.

    Args:
        reservation: instance Reservation đã cập nhật status.
        old_status: trạng thái cũ (string) nếu có.
    """
    if not reservation.customer_email:
        logger.warning(
            'Bỏ qua gửi mail cập nhật đặt bàn #%s: không có email khách.',
            reservation.id,
        )
        return False

    try:
        new_status = reservation.status
        new_status_display = RESERVATION_STATUS_MAP.get(new_status, new_status)
        old_status_display = RESERVATION_STATUS_MAP.get(old_status, old_status) if old_status else None

        subject = f'📅 Đặt bàn #{reservation.id} — {new_status_display}'

        context = {
            'reservation': reservation,
            'branch_name': _get_safe_branch_name(reservation),
            'old_status_display': old_status_display,
            'new_status_display': new_status_display,
            'status_color': STATUS_COLORS.get(new_status, '#6c757d'),
            'status_message': RESERVATION_STATUS_MESSAGES.get(new_status, ''),
        }

        html_content = render_to_string(
            'cafe/emails/reservation_status_update.html', context
        )

        text_content = (
            f'Cập nhật đặt bàn #{reservation.id}\n'
            f'Trạng thái mới: {new_status_display}\n'
        )
        if old_status_display:
            text_content += f'Trạng thái cũ: {old_status_display}\n'
        text_content += (
            f'Chi nhánh: {_get_safe_branch_name(reservation)}\n'
            f'Ngày: {reservation.date} — Giờ: {reservation.time}\n'
            f'Số người: {reservation.guests}\n'
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[reservation.customer_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            'Đã gửi mail cập nhật đặt bàn #%s (%s → %s) đến %s',
            reservation.id, old_status or '?', new_status, reservation.customer_email,
        )
        return True

    except Exception as e:
        logger.error(
            'Lỗi gửi mail cập nhật đặt bàn #%s: %s',
            reservation.id, str(e),
        )
        return False


# ==================== ORDER ====================

def send_order_confirmation_email(order):
    """
    Gửi email xác nhận đơn hàng cho khách.

    Args:
        order: instance Order vừa tạo.
    """
    if not order.customer_email:
        logger.warning(
            'Bỏ qua gửi mail xác nhận đơn #%s: không có email khách.',
            order.id,
        )
        return False

    try:
        subject = f'📦 Xác nhận đơn hàng #{order.id} — CafeManager'

        # Lấy danh sách món
        from cafe.models import OrderItem
        items = OrderItem.objects.filter(order=order).select_related('product')
        for item in items:
            item.subtotal = f'{item.price * item.quantity:,}'.replace(',', '.')

        context = {
            'order': order,
            'items': items,
            'branch_name': _get_safe_branch_name(order),
            'order_type_display': ORDER_TYPE_MAP.get(order.order_type, order.order_type),
            'payment_display': PAYMENT_MAP.get(order.payment_method, order.payment_method),
            'status_display': ORDER_STATUS_MAP.get(order.status, order.status),
        }

        html_content = render_to_string(
            'cafe/emails/order_confirmation.html', context
        )

        # Plain text fallback
        text_lines = [
            f'Xác nhận đơn hàng #{order.id}',
            f'Khách: {order.customer_name}',
            f'SĐT: {order.customer_phone}',
            f'Loại đơn: {ORDER_TYPE_MAP.get(order.order_type, order.order_type)}',
        ]
        if order.customer_address:
            text_lines.append(f'Địa chỉ giao: {order.customer_address}')
        text_lines.append(f'Tổng tiền: {order.total_price:,}đ'.replace(',', '.'))
        text_lines.append(f'Trạng thái: {ORDER_STATUS_MAP.get(order.status, order.status)}')
        text_lines.append('')
        text_lines.append('Chi tiết món:')
        for item in items:
            text_lines.append(f'  - {item.product.name} x{item.quantity} = {item.subtotal}đ')

        text_content = '\n'.join(text_lines)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.customer_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            'Đã gửi mail xác nhận đơn #%s đến %s',
            order.id, order.customer_email,
        )
        return True

    except Exception as e:
        logger.error(
            'Lỗi gửi mail xác nhận đơn #%s: %s',
            order.id, str(e),
        )
        return False


def send_order_status_update_email(order, old_status=None):
    """
    Gửi email cập nhật trạng thái đơn hàng.

    Args:
        order: instance Order đã cập nhật status.
        old_status: trạng thái cũ (string) nếu có.
    """
    if not order.customer_email:
        logger.warning(
            'Bỏ qua gửi mail cập nhật đơn #%s: không có email khách.',
            order.id,
        )
        return False

    try:
        new_status = order.status
        new_status_display = ORDER_STATUS_MAP.get(new_status, new_status)
        old_status_display = ORDER_STATUS_MAP.get(old_status, old_status) if old_status else None

        subject = f'🔄 Đơn hàng #{order.id} — {new_status_display}'

        context = {
            'order': order,
            'old_status_display': old_status_display,
            'new_status_display': new_status_display,
            'status_color': STATUS_COLORS.get(new_status, '#6c757d'),
            'status_message': ORDER_STATUS_MESSAGES.get(new_status, ''),
        }

        html_content = render_to_string(
            'cafe/emails/order_status_update.html', context
        )

        text_content = (
            f'Cập nhật đơn hàng #{order.id}\n'
            f'Trạng thái mới: {new_status_display}\n'
        )
        if old_status_display:
            text_content += f'Trạng thái cũ: {old_status_display}\n'
        text_content += (
            f'Tổng tiền: {order.total_price:,}đ\n'.replace(',', '.')
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.customer_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            'Đã gửi mail cập nhật đơn #%s (%s → %s) đến %s',
            order.id, old_status or '?', new_status, order.customer_email,
        )
        return True

    except Exception as e:
        logger.error(
            'Lỗi gửi mail cập nhật đơn #%s: %s',
            order.id, str(e),
        )
        return False


# ==================== PASSWORD RESET ====================

def send_password_reset_email(email, username, reset_url):
    """
    Gửi email đặt lại mật khẩu.

    Args:
        email: Email người dùng
        username: Tên đăng nhập
        reset_url: Link đặt lại mật khẩu
    """
    try:
        subject = '🔐 Đặt lại mật khẩu — CafeManager'

        context = {
            'username': username,
            'reset_url': reset_url,
        }

        html_content = render_to_string(
            'cafe/emails/password_reset.html', context
        )

        # Plain text fallback
        text_content = (
            f'Xin chào {username},\n\n'
            f'Bạn đã yêu cầu đặt lại mật khẩu.\n\n'
            f'Vui lòng click vào link sau để đặt lại mật khẩu:\n'
            f'{reset_url}\n\n'
            f'Link này có hiệu lực trong 1 giờ.\n\n'
            f'Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.\n\n'
            f'Trân trọng,\n'
            f'CafeManager Team'
        )

        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_msg.attach_alternative(html_content, 'text/html')
        email_msg.send(fail_silently=False)

        logger.info(
            'Đã gửi mail đặt lại mật khẩu đến %s', email,
        )
        return True

    except Exception as e:
        logger.error(
            'Lỗi gửi mail đặt lại mật khẩu đến %s: %s',
            email, str(e),
        )
        return False

