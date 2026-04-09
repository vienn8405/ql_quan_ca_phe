from django.contrib import admin
from .models import (
    CafeBranch, Inventory, RawMaterial, BranchMaterialStock, ProductRecipe,
    StockLog, Supplier, SupplierOrder,
    Product, Category, Employee, Voucher, Table,
    Attendance, WorkShift, ShiftAssignment,
    CustomerProfile, Reservation, Review,
)

# ====== Chi nhánh ======
@admin.register(CafeBranch)
class CafeBranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address")

# ====== Sản phẩm & danh mục ======
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "category")
    list_filter = ("category",)
    search_fields = ("name",)

# ====== Kho thành phẩm ======
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity", "updated_at")
    search_fields = ("product__name",)
    ordering = ("product__name",)

# ====== Kho nguyên vật liệu ======
@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "quantity", "unit", "min_quantity", "updated_at")
    list_filter = ("unit",)
    search_fields = ("name",)

@admin.register(BranchMaterialStock)
class BranchMaterialStockAdmin(admin.ModelAdmin):
    list_display = ("id", "material", "branch", "quantity", "min_quantity", "updated_at")
    list_filter = ("branch",)
    search_fields = ("material__name", "branch__name")

# ====== Công thức pha chế ======
@admin.register(ProductRecipe)
class ProductRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "material", "quantity_required")
    list_filter = ("product",)
    search_fields = ("product__name", "material__name")

# ====== Lịch sử nhập/xuất kho ======
@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ("id", "stock_type", "action", "branch", "product", "material", "quantity", "created_at", "note")
    list_filter = ("stock_type", "action", "branch")
    search_fields = ("product__name", "material__name", "branch__name", "note")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

# ====== Nhà cung cấp ======
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact_person", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone")

# ====== Lịch sử nhập hàng từ NCC ======
@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "ingredient", "quantity", "unit_price", "total_price", "order_date")
    list_filter = ("supplier", "order_date")
    search_fields = ("supplier__name", "ingredient__name")
    ordering = ("-order_date",)

# ====== Nhân viên & chấm công ======
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "role", "phone", "salary")
    search_fields = ("name", "role")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "date", "check_in", "check_out")
    list_filter = ("date",)
    search_fields = ("employee__name",)

@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "shift_type", "date")
    list_filter = ("shift_type", "branch")

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "shift")
    search_fields = ("employee__name",)

# ====== Voucher & Bàn ======
@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "discount_type", "discount_value", "used_count", "max_uses", "is_active", "expired_at")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "area", "capacity", "status", "branch")
    list_filter = ("status", "branch")

# ====== Khách hàng thân thiết ======
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "rank", "total_spent", "points")
    list_filter = ("rank",)
    search_fields = ("name", "phone")

# ====== Đặt bàn & Đánh giá ======
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_phone", "branch", "date", "time", "status")
    list_filter = ("status", "branch")
    search_fields = ("customer_name", "customer_phone")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "customer_name", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("customer_name", "product__name")
