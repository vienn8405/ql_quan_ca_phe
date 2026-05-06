from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone

# Create your models here.
class User(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Quản trị viên'),
        ('cashier', 'Thu ngân'),
        ('shipper', 'Giao hàng'),
        ('customer', 'Khách hàng'),
    )

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)  # giữ tương thích ngược
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    # Fields for password reset
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

#loại sản phẩm
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ==================== SHIPPER PROFILE ====================

class ShipperProfile(models.Model):
    """
    Profile mở rộng cho tài khoản shipper.
    Mỗi User với role='shipper' có một ShipperProfile tương ứng.
    """
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='shipper_profile'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại')
    
    # Chi nhánh shipper phụ trách
    assigned_branch = models.ForeignKey(
        'CafeBranch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shippers'
    )
    
    # Trạng thái khả dụng
    is_available = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    
    # Số đơn tối đa có thể nhận cùng lúc
    max_active_orders = models.IntegerField(default=5, verbose_name='Số đơn tối đa cùng lúc')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Shipper'
        verbose_name_plural = 'Shipper Profiles'
    
    def __str__(self):
        return f"{self.user.username} ({self.assigned_branch.name if self.assigned_branch else 'Chưa gán chi nhánh'})"
    
    def get_active_orders_count(self):
        """Đếm số đơn đang hoạt động của shipper"""
        from .models import Order
        return Order.objects.filter(
            assigned_shipper=self.user,
            delivery_status__in=['assigned', 'accepted', 'shipping']
        ).count()
    
    def can_accept_more_orders(self):
        """Kiểm tra shipper còn slot nhận đơn"""
        return self.get_active_orders_count() < self.max_active_orders

#tên món  
class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.IntegerField()

     # thêm ảnh 
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,      
        blank=True      
    )

    def __str__(self):
        return self.name
    

 #đơn hàng   
class Order(models.Model):
    PAYMENT_CHOICES = (
        ("cash", "Tiền mặt"),
        ("stripe", "Stripe"),
    )

    STATUS_CHOICES = (
        ("pending", "Chờ xử lý"),
        ("confirmed", "Đã xác nhận"),
        ("preparing", "Đang pha chế"),
        ("ready_for_delivery", "Chờ lấy hàng"),
        ("delivering", "Đang giao"),
        ("completed", "Hoàn tất"),
        ("cancelled", "Đã hủy"),
    )

    ORDER_TYPE_CHOICES = (
        ("dine_in", "Tại quán"),
        ("takeaway", "Mang đi"),
        ("delivery", "Giao hàng"),
    )

    DELIVERY_STATUS_CHOICES = (
        ("not_required", "Không áp dụng"),
        ("waiting", "Chờ gán shipper"),
        ("assigned", "Đã gán shipper / Chờ nhận"),
        ("accepted", "Shipper đã nhận đơn"),
        ("shipping", "Đang giao"),
        ("delivered", "Đã giao"),
        ("failed", "Giao thất bại"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.IntegerField(default=0)

    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(max_length=254, blank=True, null=True, verbose_name='Email khách hàng')
    customer_address = models.CharField(max_length=255, blank=True)
    customer_lat = models.FloatField(null=True, blank=True)
    customer_lng = models.FloatField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default="cash",
    )
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Stripe Checkout Session ID"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default="takeaway",
    )

    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default="not_required",
    )

    delivery_fee = models.IntegerField(default=0)
    delivery_distance = models.FloatField(default=0)  # mét
    discount_amount = models.IntegerField(default=0)  # số tiền giảm từ voucher
    assigned_shipper = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_delivery_orders'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    delivery_attempt_count = models.IntegerField(default=0)

    # chi nhánh xử lý đơn
    branch = models.ForeignKey(
         'CafeBranch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # bàn (cho đơn dine_in)
    table = models.ForeignKey(
        'Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # voucher áp dụng
    voucher = models.ForeignKey(
        'Voucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

#chi tiết đơn hàng
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    
#quản lí kho
class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.name

#quản lí nhân viên
class Employee(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    salary = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#tool 1 chi nhánh quán
class CafeBranch(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    open_time = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='branches/', null=True, blank=True)

    # bán kính giao hàng (mét)
    delivery_radius = models.FloatField(default=3000)

    is_active = models.BooleanField(default=True)

    location = gis_models.PointField(srid=4326, geography=True)

    def __str__(self):
        return self.name


class RawMaterial(models.Model):
    UNIT_CHOICES = (
        ('g', 'Gram'),
        ('ml', 'Ml'),
        ('item', 'Cái'),
    )

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='g')
    quantity = models.FloatField(default=0)
    min_quantity = models.FloatField(default=0)  # cảnh báo sắp hết
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"


class BranchMaterialStock(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='branch_stocks')
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE, related_name='material_stocks')
    quantity = models.FloatField(default=0)
    min_quantity = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('material', 'branch')

    def __str__(self):
        return f"{self.material.name} - {self.branch.name}"
    
class ProductRecipe(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    quantity_required = models.FloatField(default=0)

    class Meta:
        unique_together = ('product', 'material')

    def __str__(self):
        return f"{self.product.name} - {self.material.name}"
    
class StockLog(models.Model):
    STOCK_TYPE_CHOICES = (
        ('finished', 'Thành phẩm'),
        ('material', 'Nguyên vật liệu'),
    )

    ACTION_CHOICES = (
        ('import', 'Nhập kho'),
        ('export', 'Xuất kho'),
        ('make', 'Pha chế'),
        ('order', 'Bán hàng'),
    )

    stock_type = models.CharField(max_length=20, choices=STOCK_TYPE_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(RawMaterial, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(CafeBranch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.FloatField(default=0)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock_type} - {self.action}"


# quản lý bàn
class Table(models.Model):
    STATUS_CHOICES = (
        ('available', 'Trống'),
        ('occupied', 'Đang dùng'),
        ('reserved', 'Đã đặt trước'),
    )
    number = models.CharField(max_length=10)  # Số bàn / tên bàn
    area = models.CharField(max_length=50, blank=True)  # Khu vực (trong/ngoài/VIP)
    capacity = models.IntegerField(default=4)  # Sức chứa
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    branch = models.ForeignKey('CafeBranch', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Bàn {self.number} ({self.get_status_display()})"


# khuyến mãi / voucher
class Voucher(models.Model):
    TYPE_CHOICES = (
        ('percent', 'Phần trăm (%)'),
        ('fixed', 'Số tiền cố định (VNĐ)'),
    )
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='percent')
    discount_value = models.IntegerField(default=0)  # % hoặc VNĐ
    min_order_value = models.IntegerField(default=0)  # đơn tối thiểu
    max_uses = models.IntegerField(default=100)        # tổng số lần dùng
    used_count = models.IntegerField(default=0)
    expired_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Áp dụng chi nhánh")
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, order_total=0, branch_id=None):
        """Kiểm tra voucher còn hiệu lực không"""
        if not self.is_active:
            return False, 'Voucher không hoạt động'
        if self.used_count >= self.max_uses:
            return False, 'Voucher đã hết lượt sử dụng'
        if self.expired_at and timezone.now() > self.expired_at:
            return False, 'Voucher đã hết hạn'
        if order_total < self.min_order_value:
            return False, f'Đơn tối thiểu {self.min_order_value:,}đ để dùng voucher này'
        
        # Check chi nhánh hợp lệ
        if self.branch and branch_id:
            if str(self.branch.id) != str(branch_id):
                return False, f'Voucher chỉ áp dụng tại chi nhánh {self.branch.name}'
                
        return True, ''

    def calc_discount(self, order_total):
        """Tính số tiền được giảm"""
        if self.discount_type == 'percent':
            return int(order_total * self.discount_value / 100)
        return min(self.discount_value, order_total)

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()} {self.discount_value}"


# chấm công nhân viên
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    @property
    def work_hours(self):
        """Tính số giờ làm trong ngày"""
        if self.check_in and self.check_out:
            from datetime import datetime, date
            dt_in = datetime.combine(date.today(), self.check_in)
            dt_out = datetime.combine(date.today(), self.check_out)
            delta = dt_out - dt_in
            return float(f"{delta.seconds / 3600:.1f}")
        return 0

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

# ================= TÍNH NĂNG MỚI =================

# 1. Khách hàng thân thiết / Tích điểm
class CustomerProfile(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)
    total_spent = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    
    # Hạng (Bronze/Silver/Gold) tùy logic
    rank = models.CharField(max_length=50, default='Đồng')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_rank(self):
        # Ví dụ: trên 3tr -> Vàng (giảm 10%), trên 1tr -> Bạc (giảm 5%), dưới 1tr -> Đồng (0%)
        if self.total_spent >= 3000000:
            self.rank = 'Vàng'
        elif self.total_spent >= 1000000:
            self.rank = 'Bạc'
        else:
            self.rank = 'Đồng'
        self.save()

    def __str__(self):
        return f"{self.name or self.phone} ({self.rank})"

# 2. Đặt bàn trước
class Reservation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Chờ duyệt"),
        ("confirmed", "Đã xác nhận"),
        ("seated", "Khách đã nhận bàn"),
        ("completed", "Đã hoàn thành"),
        ("cancelled", "Đã hủy"),
        ("expired", "Hết hạn giữ bàn"),
    )
    
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(max_length=254, blank=True, null=True, verbose_name='Email khách hàng')
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE)
    
    # Bàn có thể được gán sau bởi Admin, hoặc Khách có thể chọn luôn
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField()
    time = models.TimeField()
    guests = models.IntegerField(default=2)
    note = models.TextField(blank=True, null=True)
    
    # Pre-order và Deposit
    is_preordered = models.BooleanField(default=False)
    deposit_amount = models.IntegerField(default=0)
    is_deposit_paid = models.BooleanField(default=False)
    order = models.OneToOneField('Order', on_delete=models.SET_NULL, null=True, blank=True)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Đặt bàn: {self.customer_name} - {self.date} {self.time}"

# 3. Đánh giá (Review) cho Đơn hàng - REVIEW MÓN
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    rating = models.IntegerField(default=5)  # Từ 1 đến 5 sao
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review cho Đơn #{self.order.id} - {self.rating} sao"


# ==================== REVIEW MỞ RỘNG ====================
# 3.1. Review Đơn Hàng - Customer đánh giá tổng thể đơn hàng
class OrderReview(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order_review')
    rating = models.IntegerField(default=5)  # 1-5 sao
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review Đơn #{self.order.id} - {self.rating} sao"


# 3.2. Review Shipper - Customer đánh giá shipper giao hàng
class ShipperReview(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipper_review')
    shipper = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shipper_reviews')
    rating = models.IntegerField(default=5)  # 1-5 sao
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        shipper_name = self.shipper.username if self.shipper else 'N/A'
        return f"Review Shipper {shipper_name} - {self.rating} sao"


# 3.3. Review Chi Nhánh - Customer đánh giá chi nhánh xử lý đơn
class BranchReview(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='branch_review')
    branch = models.ForeignKey(CafeBranch, on_delete=models.SET_NULL, null=True, related_name='branch_reviews')
    rating = models.IntegerField(default=5)  # 1-5 sao
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else 'N/A'
        return f"Review Chi Nhánh {branch_name} - {self.rating} sao"

# Nhà cung cấp
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Lịch sử nhập hàng từ nhà cung cấp
class SupplierOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='orders')
    ingredient = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit_price = models.IntegerField()
    total_price = models.IntegerField()
    order_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Nhập {self.ingredient.name} từ {self.supplier.name} ({self.order_date})"

# Ca làm việc
class WorkShift(models.Model):
    SHIFT_CHOICES = (
        ("morning", "Ca sáng (6h-14h)"),
        ("afternoon", "Ca chiều (14h-22h)"),
        ("evening", "Ca tối (22h-6h)"),
    )
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE)
    shift_type = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_shift_type_display()} - {self.branch.name} ({self.date})"

    class Meta:
        unique_together = ['branch', 'shift_type', 'date']

# Phân công nhân viên vào ca
class ShiftAssignment(models.Model):
    shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.shift}"

    class Meta:
        unique_together = ['shift', 'employee']


# ==================== AUDIT LOG ====================

class AuditLog(models.Model):
    """Lịch sử thao tác quan trọng trên hệ thống."""
    action = models.CharField(max_length=50)  # ORDER_STATUS_CHANGED, SHIPPER_ASSIGNED, ...
    order = models.ForeignKey(
        'Order', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    actor = models.CharField(max_length=100)    # username người thực hiện
    role = models.CharField(max_length=50)     # admin, shipper, system, customer
    details = models.TextField(blank=True)      # ghi chú chi tiết
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"[{self.action}] {self.actor} ({self.role}) - {self.created_at:%H:%M %d/%m/%Y}"
