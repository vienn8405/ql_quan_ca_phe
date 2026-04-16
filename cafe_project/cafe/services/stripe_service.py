"""
Stripe Service — Tạo Checkout Session và xử lý Webhook.

Dùng Stripe Checkout (hosted page) để:
  - Tạo session thanh toán với order metadata
  - Xử lý webhook checkout.session.completed để xác nhận thanh toán
"""

import logging
import stripe as stripe_lib
from django.conf import settings

logger = logging.getLogger(__name__)

# Khởi tạo Stripe với secret key từ settings
stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
if stripe_api_key:
    stripe_lib.api_key = stripe_api_key


def get_publishable_key():
    """Trả về Stripe Publishable Key cho client-side."""
    return getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')


def create_checkout_session(order, request):
    """
    Tạo Stripe Checkout Session cho một đơn hàng.

    Args:
        order: instance Order
        request: HttpRequest (để lấy origin cho success/cancel URL)

    Returns:
        stripe_lib.checkout.Session | None
    """
    if not stripe_api_key:
        logger.error('STRIPE_SECRET_KEY chưa được cấu hình')
        return None

    try:
        origin = request.build_absolute_uri('/').rstrip('/')

        # Build line_items từ OrderItem
        from cafe.models import OrderItem
        items = OrderItem.objects.filter(order=order).select_related('product')

        stripe_currency = getattr(settings, 'STRIPE_PRICE_CURRENCY', 'vnd')
        line_items = []
        for item in items:
            line_items.append({
                'price_data': {
                    'currency': stripe_currency,
                    'unit_amount': item.price,
                    'product_data': {
                        'name': item.product.name,
                    },
                },
                'quantity': item.quantity,
            })

        if not line_items:
            logger.error('Order #%s không có items để tạo Checkout Session', order.id)
            return None

        session = stripe_lib.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{origin}/order/stripe-success/?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
            cancel_url=f"{origin}/order/stripe-cancel/?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
            metadata={
                'order_id': str(order.id),
            },
            customer_email=order.customer_email or None,
        )

        # Lưu session_id vào order
        order.stripe_checkout_session_id = session.id
        order.save(update_fields=['stripe_checkout_session_id'])

        logger.info('Tạo Stripe Checkout Session %s cho Order #%s', session.id, order.id)
        return session

    except stripe_lib.error.StripeError as e:
        logger.error('Stripe error khi tạo Checkout Session cho Order #%s: %s', order.id, str(e))
        return None
    except Exception as e:
        logger.error('Lỗi không xác định khi tạo Checkout Session cho Order #%s: %s', order.id, str(e))
        return None


def retrieve_checkout_session(session_id):
    """
    Lấy thông tin Checkout Session từ Stripe.

    Args:
        session_id: string Stripe session ID

    Returns:
        stripe_lib.checkout.Session | None
    """
    if not stripe_api_key:
        return None

    try:
        return stripe_lib.checkout.Session.retrieve(session_id)
    except stripe_lib.error.StripeError as e:
        logger.error('Stripe error khi retrieve session %s: %s', session_id, str(e))
        return None


def construct_webhook_event(payload, sig_header, webhook_secret):
    """
    Xác thực và parse webhook payload từ Stripe.

    Args:
        payload: raw request body (bytes)
        sig_header: request.META['HTTP_STRIPE_SIGNATURE']
        webhook_secret: settings.STRIPE_WEBHOOK_SECRET

    Returns:
        stripe_lib.Event | None
    """
    if not stripe_api_key or not webhook_secret:
        logger.error('STRIPE_SECRET_KEY hoặc STRIPE_WEBHOOK_SECRET chưa được cấu hình')
        return None

    try:
        return stripe_lib.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe_lib.error.SignatureVerificationError:
        logger.error('Webhook signature verification failed')
        return None
    except Exception as e:
        logger.error('Lỗi khi construct webhook event: %s', str(e))
        return None


def handle_checkout_completed(event):
    """
    Xử lý event checkout.session.completed.
    Tìm Order qua stripe_checkout_session_id trong DB và set is_paid=True.

    Args:
        event: stripe_lib.Event

    Returns:
        True nếu xử lý thành công, False nếu không
    """
    session = event.data.object
    session_id = session.id

    logger.info('Webhook: checkout.session.completed — session_id=%s', session_id)

    # Tìm order bằng stripe_checkout_session_id ( không phụ thuộc session client)
    from cafe.models import Order
    try:
        order = Order.objects.get(stripe_checkout_session_id=session_id)
    except Order.DoesNotExist:
        logger.error('Không tìm thấy Order với stripe_checkout_session_id=%s', session_id)
        return False

    if order.is_paid:
        logger.info('Order #%s đã được đánh dấu is_paid=True trước đó, bỏ qua', order.id)
        return True

    order.is_paid = True
    order.save(update_fields=['is_paid'])

    logger.info('Webhook: Order #%s — is_paid=True (via Stripe Checkout %s)', order.id, session_id)

    # Gửi email xác nhận thanh toán (nếu có email)
    from .email_service import send_order_status_update_email
    try:
        send_order_status_update_email(order, old_status=None)
    except Exception as e:
        logger.warning('Webhook: gửi mail sau thanh toán Stripe cho Order #%s thất bại: %s', order.id, str(e))

    # Audit log
    try:
        from cafe.models import AuditLog
        AuditLog.objects.create(
            action='ORDER_PAID_STRIPE',
            order=order,
            actor='stripe_webhook',
            role='system',
            details=f'Thanh toán Stripe thành công. Session: {session_id}',
        )
    except Exception as e:
        print(f"[AUDIT_LOG_ERROR] {e}")

    return True
