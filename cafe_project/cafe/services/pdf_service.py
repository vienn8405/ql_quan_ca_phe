"""
Service tạo file PDF cho hệ thống quản lý quán cà phê.
Sử dụng reportlab để render PDF hóa đơn đơn hàng.
"""
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os

# ======================== FONT TIẾNG VIỆT ========================

def _register_fonts():
    """Đăng ký font hỗ trợ tiếng Việt. Ưu tiên DejaVu (có sẵn trên hầu hết hệ thống)."""
    font_registered = False

    # Thử DejaVuSans (phổ biến nhất trên Windows/Linux)
    dejavu_paths = [
        os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf'),
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/tahoma.ttf',
    ]
    dejavu_bold_paths = [
        os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans-Bold.ttf'),
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/tahomabd.ttf',
    ]

    for path in dejavu_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('VNFont', path))
                font_registered = True
                break
            except Exception:
                continue

    if font_registered:
        for path in dejavu_bold_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('VNFontBold', path))
                    return 'VNFont', 'VNFontBold'
                except Exception:
                    continue
        return 'VNFont', 'VNFont'

    # Fallback: dùng Helvetica (không hỗ trợ tiếng Việt hoàn chỉnh)
    return 'Helvetica', 'Helvetica-Bold'


FONT_NAME, FONT_BOLD = _register_fonts()


# ======================== HELPER FORMAT TIỀN ========================

def fmt_vnd(value):
    """Format số tiền kiểu Việt Nam: 150.000đ"""
    try:
        val = int(value)
    except (ValueError, TypeError):
        return '0đ'
    if val == 0:
        return '0đ'
    formatted = '{:,.0f}'.format(val).replace(',', '.')
    return f'{formatted}đ'


# ======================== EXPORT PDF HÓA ĐƠN ========================

def export_order_pdf(order, items):
    """
    Tạo file PDF hóa đơn cho đơn hàng.

    Args:
        order: Order instance
        items: QuerySet/list của OrderItem

    Returns:
        HttpResponse chứa file PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    # ===== STYLES =====
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Title'],
        fontName=FONT_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#5B3A1A'),
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )
    style_subtitle = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        textColor=colors.gray,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )
    style_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName=FONT_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#5B3A1A'),
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )
    style_normal = ParagraphStyle(
        'NormalVN',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
    )
    style_bold = ParagraphStyle(
        'BoldVN',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=14,
    )
    style_right = ParagraphStyle(
        'RightVN',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        alignment=TA_RIGHT,
    )
    style_right_bold = ParagraphStyle(
        'RightBoldVN',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#5B3A1A'),
    )
    style_footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.gray,
        alignment=TA_CENTER,
        spaceBefore=8 * mm,
    )

    # ===== BUILD CONTENT =====
    content = []

    # --- HEADER ---
    content.append(Paragraph('CafeFlow', style_title))
    content.append(Paragraph('Smart Coffee Management', style_subtitle))

    # Separator
    content.append(HRFlowable(
        width='100%', thickness=1.5,
        color=colors.HexColor('#5B3A1A'),
        spaceAfter=4 * mm, spaceBefore=2 * mm,
    ))

    content.append(Paragraph(f'HOA DON DON HANG #{order.id}', ParagraphStyle(
        'InvHeader', parent=style_title, fontSize=14, spaceAfter=2 * mm,
    )))

    # Ngày tạo
    date_str = order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else ''
    content.append(Paragraph(f'Ngay: {date_str}', ParagraphStyle(
        'DateLine', parent=style_subtitle, fontSize=10, spaceAfter=4 * mm,
    )))

    # --- THÔNG TIN ĐƠN HÀNG ---
    content.append(Paragraph('THONG TIN DON HANG', style_heading))

    # Map display values
    order_type_map = dict(getattr(order.__class__, 'ORDER_TYPE_CHOICES', []))
    status_map = dict(getattr(order.__class__, 'STATUS_CHOICES', []))
    delivery_status_map = dict(getattr(order.__class__, 'DELIVERY_STATUS_CHOICES', []))
    payment_map = dict(getattr(order.__class__, 'PAYMENT_CHOICES', []))

    info_data = [
        ['Loai don:', order_type_map.get(order.order_type, order.order_type)],
        ['Trang thai:', status_map.get(order.status, order.status)],
        ['Thanh toan:', payment_map.get(order.payment_method, order.payment_method)],
    ]

    if order.branch:
        info_data.append(['Chi nhanh:', order.branch.name])

    if order.order_type == 'delivery':
        info_data.append([
            'Giao hang:',
            delivery_status_map.get(order.delivery_status, order.delivery_status)
        ])

    info_table = Table(info_data, colWidths=[35 * mm, 130 * mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#5B3A1A')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 3 * mm))

    # --- THÔNG TIN KHÁCH HÀNG ---
    content.append(Paragraph('THONG TIN KHACH HANG', style_heading))

    cust_data = [
        ['Ten:', order.customer_name or 'Khach vang lai'],
        ['SDT:', order.customer_phone or 'Khong co'],
    ]
    if order.customer_address:
        cust_data.append(['Dia chi:', order.customer_address])
    if order.note:
        cust_data.append(['Ghi chu:', order.note])

    cust_table = Table(cust_data, colWidths=[35 * mm, 130 * mm])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#5B3A1A')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    content.append(cust_table)
    content.append(Spacer(1, 4 * mm))

    # --- DANH SÁCH MÓN ---
    content.append(Paragraph('CHI TIET MON DA DAT', style_heading))

    # Table header
    table_data = [
        [
            Paragraph('STT', style_bold),
            Paragraph('San pham', style_bold),
            Paragraph('SL', style_bold),
            Paragraph('Don gia', style_bold),
            Paragraph('Thanh tien', style_bold),
        ]
    ]

    subtotal_all = 0
    for idx, item in enumerate(items, 1):
        item_subtotal = item.quantity * item.price
        subtotal_all += item_subtotal
        table_data.append([
            Paragraph(str(idx), style_normal),
            Paragraph(str(item.product.name), style_normal),
            Paragraph(str(item.quantity), style_normal),
            Paragraph(fmt_vnd(item.price), style_right),
            Paragraph(fmt_vnd(item_subtotal), style_right),
        ])

    items_table = Table(
        table_data,
        colWidths=[12 * mm, 70 * mm, 15 * mm, 35 * mm, 35 * mm],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B3A1A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0b09a')),
        # Alternating row colors
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f0eb')),
            ]))

    content.append(items_table)
    content.append(Spacer(1, 4 * mm))

    # --- TỔNG KẾT ---
    content.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#c0b09a'),
        spaceAfter=3 * mm, spaceBefore=2 * mm,
    ))

    summary_data = []
    summary_data.append(['Tam tinh:', fmt_vnd(subtotal_all)])

    delivery_fee = getattr(order, 'delivery_fee', 0) or 0
    if delivery_fee > 0:
        summary_data.append(['Phi giao hang:', fmt_vnd(delivery_fee)])

    discount_amount = getattr(order, 'discount_amount', 0) or 0
    if discount_amount > 0:
        summary_data.append(['Giam gia:', f'-{fmt_vnd(discount_amount)}'])

    if order.voucher:
        voucher_desc = f'Voucher: {order.voucher.code}'
        summary_data.append(['Khuyen mai:', voucher_desc])

    summary_data.append(['TONG TIEN:', fmt_vnd(order.total_price)])

    summary_table = Table(summary_data, colWidths=[125 * mm, 42 * mm])
    summary_styles = [
        ('FONTNAME', (0, 0), (0, -1), FONT_NAME),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        # Last row = bold total
        ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#5B3A1A')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#5B3A1A')),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
    ]
    summary_table.setStyle(TableStyle(summary_styles))
    content.append(summary_table)

    # --- FOOTER ---
    content.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#c0b09a'),
        spaceAfter=4 * mm, spaceBefore=6 * mm,
    ))
    content.append(Paragraph('Cam on quy khach da su dung dich vu CafeFlow!', style_footer))
    content.append(Paragraph('Hen gap lai!', style_footer))

    # ===== GENERATE PDF =====
    doc.build(content)

    buffer.seek(0)
    filename = f'hoa_don_don_hang_{order.id}.pdf'

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ======================== EXPORT PDF BÁO CÁO DOANH THU ========================

def export_revenue_pdf(data):
    """
    Tạo file PDF báo cáo doanh thu.

    Args:
        data: dict chứa các key từ revenue_report view
    """
    from datetime import datetime

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    # ===== STYLES =====
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'RevTitle', parent=styles['Title'],
        fontName=FONT_BOLD, fontSize=18,
        textColor=colors.HexColor('#5B3A1A'),
        alignment=TA_CENTER, spaceAfter=4 * mm,
    )
    style_subtitle = ParagraphStyle(
        'RevSubtitle', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=10,
        textColor=colors.gray, alignment=TA_CENTER,
        spaceAfter=2 * mm,
    )
    style_heading = ParagraphStyle(
        'RevHeading', parent=styles['Heading3'],
        fontName=FONT_BOLD, fontSize=12,
        textColor=colors.HexColor('#5B3A1A'),
        spaceBefore=6 * mm, spaceAfter=3 * mm,
    )
    style_normal = ParagraphStyle(
        'RevNormal', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=10, leading=14,
    )
    style_bold = ParagraphStyle(
        'RevBold', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=10, leading=14,
    )
    style_right = ParagraphStyle(
        'RevRight', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=10, alignment=TA_RIGHT,
    )
    style_footer = ParagraphStyle(
        'RevFooter', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=9,
        textColor=colors.gray, alignment=TA_CENTER,
        spaceBefore=8 * mm,
    )

    content = []

    # --- HEADER ---
    content.append(Paragraph('CafeFlow', style_title))
    content.append(Paragraph('Smart Coffee Management', style_subtitle))

    content.append(HRFlowable(
        width='100%', thickness=1.5,
        color=colors.HexColor('#5B3A1A'),
        spaceAfter=4 * mm, spaceBefore=2 * mm,
    ))

    content.append(Paragraph('BAO CAO DOANH THU', ParagraphStyle(
        'RevMainTitle', parent=style_title, fontSize=15, spaceAfter=2 * mm,
    )))

    # Thời gian
    ts = datetime.now().strftime('%d/%m/%Y %H:%M')
    content.append(Paragraph(f'Ngay xuat: {ts}', style_subtitle))

    date_from = data.get('date_from', '')
    date_to = data.get('date_to', '')
    content.append(Paragraph(f'Thoi gian: {date_from} den {date_to}', ParagraphStyle(
        'RevDateRange', parent=style_subtitle, spaceAfter=5 * mm,
    )))

    # --- TỔNG QUAN ---
    content.append(Paragraph('TONG QUAN', style_heading))

    total_revenue = data.get('total_revenue', 0)
    total_orders = data.get('total_orders', 0)
    avg_daily = data.get('avg_daily', 0)

    summary_data = [
        [Paragraph('Tong doanh thu:', style_bold), Paragraph(fmt_vnd(total_revenue), style_right)],
        [Paragraph('Tong so don hoan thanh:', style_bold), Paragraph(str(total_orders), style_right)],
        [Paragraph('TB doanh thu / ngay:', style_bold), Paragraph(fmt_vnd(avg_daily), style_right)],
    ]

    summary_table = Table(summary_data, colWidths=[100 * mm, 67 * mm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0d5c8')),
        # First row highlight
        ('FONTNAME', (1, 0), (1, 0), FONT_BOLD),
        ('FONTSIZE', (1, 0), (1, 0), 13),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#5B3A1A')),
    ]))
    content.append(summary_table)
    content.append(Spacer(1, 3 * mm))

    # --- DOANH THU THEO NGÀY ---
    labels = data.get('labels', [])
    revenues = data.get('revenues', [])
    order_counts = data.get('order_counts', [])

    if labels:
        content.append(Paragraph('DOANH THU THEO NGAY', style_heading))

        daily_data = [
            [
                Paragraph('Ngay', style_bold),
                Paragraph('Doanh thu', style_bold),
                Paragraph('So don', style_bold),
            ]
        ]
        for i, label in enumerate(labels):
            daily_data.append([
                Paragraph(label, style_normal),
                Paragraph(fmt_vnd(revenues[i] if i < len(revenues) else 0), style_right),
                Paragraph(str(order_counts[i] if i < len(order_counts) else 0), style_normal),
            ])

        daily_table = Table(daily_data, colWidths=[40 * mm, 70 * mm, 57 * mm], repeatRows=1)
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B3A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0b09a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        for i in range(1, len(daily_data)):
            if i % 2 == 0:
                daily_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f0eb')),
                ]))
        content.append(daily_table)
        content.append(Spacer(1, 3 * mm))

    # --- TOP SẢN PHẨM ---
    top_products = data.get('top_products', [])
    if top_products:
        content.append(Paragraph('TOP SAN PHAM BAN CHAY', style_heading))

        prod_data = [
            [
                Paragraph('#', style_bold),
                Paragraph('San pham', style_bold),
                Paragraph('So luong ban', style_bold),
            ]
        ]
        for idx, p in enumerate(top_products, 1):
            prod_data.append([
                Paragraph(str(idx), style_normal),
                Paragraph(str(p.get('product__name', '')), style_normal),
                Paragraph(str(p.get('total_qty', 0)), style_normal),
            ])

        prod_table = Table(prod_data, colWidths=[15 * mm, 107 * mm, 45 * mm], repeatRows=1)
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B3A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0b09a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        content.append(prod_table)
        content.append(Spacer(1, 3 * mm))

    # --- THEO LOẠI ĐƠN ---
    type_labels = data.get('type_labels', [])
    type_counts = data.get('type_counts', [])
    type_revenues = data.get('type_revenues', [])

    if type_labels:
        content.append(Paragraph('DOANH THU THEO LOAI DON', style_heading))

        type_data = [
            [
                Paragraph('Loai don', style_bold),
                Paragraph('So don', style_bold),
                Paragraph('Doanh thu', style_bold),
            ]
        ]
        for i, t_label in enumerate(type_labels):
            type_data.append([
                Paragraph(str(t_label), style_normal),
                Paragraph(str(type_counts[i] if i < len(type_counts) else 0), style_normal),
                Paragraph(fmt_vnd(type_revenues[i] if i < len(type_revenues) else 0), style_right),
            ])

        type_table = Table(type_data, colWidths=[55 * mm, 55 * mm, 57 * mm], repeatRows=1)
        type_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B3A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0b09a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        content.append(type_table)

    # --- FOOTER ---
    content.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#c0b09a'),
        spaceAfter=4 * mm, spaceBefore=8 * mm,
    ))
    content.append(Paragraph('Bao cao duoc tao tu dong boi he thong CafeFlow.', style_footer))

    # ===== GENERATE PDF =====
    doc.build(content)

    buffer.seek(0)
    timestamp = datetime.now().strftime('%d%m%Y_%H%M')
    filename = f'bao_cao_doanh_thu_{timestamp}.pdf'

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
