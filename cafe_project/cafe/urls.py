from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
path('', views.home, name='home'),
path('user', views.user_home, name='user_home'),
path('menu/', views.user_menu, name='user_menu'),


path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
path('register/', views.register_view, name='register'),
path('forgot-password/', views.forgot_password_view, name='forgot_password'),
path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
#admin
#sản phẩm
path('admin/products/', views.product_list, name='product_list'),
path('admin/products/add/', views.product_add, name='product_add'),
path('admin/products/delete/<int:id>/', views.product_delete, name='product_delete'),
path('admin/products/edit/<int:id>/', views.product_edit, name='product_edit'),
#đơn hàng
path('admin/orders/', views.order_list, name='order_list'),
path('admin/orders/add/', views.order_add, name='order_add'),
path('admin/orders/delete/<int:id>/', views.order_delete, name='order_delete'),
path('admin/orders/edit/<int:id>/', views.order_edit, name='order_edit'),
path('admin/orders/detail/<int:id>/', views.admin_order_detail, name='admin_order_detail'),
#loại
path('admin/categories/', views.category_list, name='category_list'),
path('admin/categories/add/', views.category_add, name='category_add'),
path('admin/categories/edit/<int:id>/', views.category_edit, name='category_edit'),
path('admin/categories/delete/<int:id>/', views.category_delete, name='category_delete'),
#kho
path('admin/inventory/', views.inventory_list, name='inventory_list'),
path('admin/inventory/edit/<int:id>/', views.inventory_edit, name='inventory_edit'),
#nhân viên
path('admin/employees/', views.employee_list, name='employee_list'),
path('admin/employees/add/', views.employee_add, name='employee_add'),
path('admin/employees/edit/<int:id>/', views.employee_edit, name='employee_edit'),
path('admin/employees/delete/<int:id>/', views.employee_delete, name='employee_delete'),

#thêm vào giỏ hàng
path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
path('cart/', views.cart, name='cart'),
path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
#đặt hàng
path('order/create/', views.user_order_create, name='user_order_create'),
#xem đơn hàng
path("order/", views.user_order_detail, name="user_order_detail"),
#view bản đồ
path("map/", views.map_view, name="map"),
path("api/branches.geojson", views.branches_geojson, name="branches_geojson"),
#quán gần nhất
path("api/near-me/", views.cafes_near_me, name="cafes_near_me"),

# chi nhánh (cafe branch)
path('admin/branches/', views.branch_list, name='branch_list'),
path('admin/branches/add/', views.branch_add, name='branch_add'),
path('admin/branches/edit/<int:id>/', views.branch_edit, name='branch_edit'),
path('admin/branches/delete/<int:id>/', views.branch_delete, name='branch_delete'),

path('admin/materials/', views.material_list, name='material_list'),
path('admin/materials/add/', views.material_add, name='material_add'),
path('admin/materials/edit/<int:id>/', views.material_edit, name='material_edit'),
path('admin/materials/delete/<int:id>/', views.material_delete, name='material_delete'),

path('admin/recipes/<int:product_id>/', views.recipe_manage, name='recipe_manage'),
path('admin/recipes/delete/<int:id>/', views.recipe_delete, name='recipe_delete'),

path('admin/inventory/make/<int:product_id>/', views.inventory_make, name='inventory_make'),

path('admin/orders/status/<int:order_id>/<str:status>/', views.order_update_status, name='order_update_status'),

path('admin/stocklogs/', views.stocklog_list, name='stocklog_list'),

path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # ===== STRIPE PAYMENT =====
    path('order/stripe-success/', views.stripe_success, name='stripe_success'),
    path('order/stripe-cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('order/stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),

    # ===== BÀN =====
    path('admin/tables/', views.table_list, name='table_list'),
    path('admin/tables/add/', views.table_add, name='table_add'),
    path('admin/tables/edit/<int:id>/', views.table_edit, name='table_edit'),
    path('admin/tables/delete/<int:id>/', views.table_delete, name='table_delete'),

    # ===== VOUCHER =====
    path('admin/vouchers/', views.voucher_list, name='voucher_list'),
    path('admin/vouchers/add/', views.voucher_add, name='voucher_add'),
    path('admin/vouchers/edit/<int:id>/', views.voucher_edit, name='voucher_edit'),
    path('admin/vouchers/delete/<int:id>/', views.voucher_delete, name='voucher_delete'),
    path('api/apply-voucher/', views.apply_voucher, name='apply_voucher'),

    # ===== CHẤM CÔNG =====
    path('admin/attendance/', views.attendance_list, name='attendance_list'),
    path('admin/attendance/edit/<int:employee_id>/', views.attendance_edit, name='attendance_edit'),
    path('admin/attendance/delete/<int:id>/', views.attendance_delete, name='attendance_delete'),

    # ===== THỐNG KÊ DOANH THU =====
    path('admin/revenue/', views.revenue_report, name='revenue_report'),

    # ===== LỌC ĐƠN HÀNG =====
    path('admin/orders/filter/', views.order_list_filtered, name='order_list_filtered'),

    # ===== TÍNH NĂNG MỚI (LOYALTY, ĐẶT BÀN, REVIEW) =====
    path('api/loyalty/check/', views.api_check_loyalty, name='api_check_loyalty'),
    path('reservation/', views.reserve_table, name='reserve_table'),
    path('admin/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin/reservations/status/<int:id>/<str:status>/', views.admin_reservation_status, name='admin_reservation_status'),
    path('order/review/<int:order_id>/<int:product_id>/', views.submit_review, name='submit_review'),
    path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
    
    # ===== REVIEW MỞ RỘNG =====
    path('order/review/order/<int:order_id>/', views.submit_order_review, name='submit_order_review'),
    path('order/review/shipper/<int:order_id>/', views.submit_shipper_review, name='submit_shipper_review'),
    path('order/review/branch/<int:order_id>/', views.submit_branch_review, name='submit_branch_review'),
    path('api/orders-heatmap/', views.api_orders_heatmap, name='api_orders_heatmap'),
    path('api/tables/available/', views.api_available_tables, name='api_available_tables'),
    path('reservation/status/', views.reservation_status, name='reservation_status'),
    path('api/branch-stats/', views.api_branch_stats, name='api_branch_stats'),

    # ===== NGHIỆP VỤ CHUYÊN NGHIỆP MỚI =====
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/suppliers/', views.supplier_list, name='supplier_list'),
    path('admin/suppliers/add/', views.supplier_add, name='supplier_add'),
    path('admin/suppliers/edit/<int:id>/', views.supplier_edit, name='supplier_edit'),
    path('admin/suppliers/delete/<int:id>/', views.supplier_delete, name='supplier_delete'),
    path('admin/shifts/', views.shift_list, name='shift_list'),
    path('admin/shifts/add/', views.shift_add, name='shift_add'),
    path('customer-history/', views.customer_history, name='customer_history'),

    # ===== SHIPPER =====
    path('shipper/deliveries/', views.shipper_deliveries, name='shipper_deliveries'),
    path('api/shipper/deliveries/', views.api_shipper_deliveries, name='api_shipper_deliveries'),
    path('shipper/deliveries/<int:order_id>/accept/', views.shipper_accept_delivery, name='shipper_accept_delivery'),
    path('shipper/deliveries/<int:order_id>/reject/', views.shipper_reject_delivery, name='shipper_reject_delivery'),
    path('shipper/deliveries/<int:order_id>/start/', views.shipper_start_delivery, name='shipper_start_delivery'),
    path('shipper/deliveries/<int:order_id>/complete/', views.shipper_complete_delivery, name='shipper_complete_delivery'),
    path('shipper/deliveries/<int:order_id>/fail/', views.shipper_fail_delivery, name='shipper_fail_delivery'),

    # ===== API TỐI ƯU =====
    path('api/optimal-branch/', views.api_optimal_branch, name='api_optimal_branch'),

    # ===== THỐNG KÊ GIS =====
    path('admin/branch-analytics/', views.branch_analytics, name='branch_analytics'),
    path('api/branch-analytics/', views.api_branch_analytics, name='api_branch_analytics'),

    # ===== IMPORT / EXPORT EXCEL =====
    path('admin/materials/import-excel/', views.import_materials_excel, name='import_materials_excel'),
    path('admin/materials/template-excel/', views.download_material_template, name='download_material_template'),
    path('admin/orders/export-excel/', views.export_orders_excel, name='export_orders_excel'),
    path('admin/orders/detail/<int:id>/export-pdf/', views.export_order_pdf, name='export_order_pdf'),
    path('admin/revenue/export-excel/', views.export_revenue_excel_view, name='export_revenue_excel'),
    path('admin/revenue/export-pdf/', views.export_revenue_pdf_view, name='export_revenue_pdf'),

    # ===== ADMIN ĐIỀU PHỐI GIAO HÀNG =====
    path('admin/deliveries/', views.admin_deliveries, name='admin_deliveries'),
    path('admin/deliveries/<int:order_id>/assign/', views.admin_assign_shipper, name='admin_assign_shipper'),

    # ===== ADMIN QUẢN LÝ SHIPPER =====
    path('admin/shippers/', views.admin_shipper_list, name='admin_shipper_list'),
    path('admin/shippers/add/', views.admin_shipper_add, name='admin_shipper_add'),
    path('admin/shippers/edit/<int:id>/', views.admin_shipper_edit, name='admin_shipper_edit'),
    path('admin/shippers/delete/<int:id>/', views.admin_shipper_delete, name='admin_shipper_delete'),
    path('admin/shippers/<int:id>/toggle-availability/', views.admin_shipper_toggle_availability, name='admin_shipper_toggle_availability'),
    path('api/shippers/by-branch/', views.api_shippers_by_branch, name='api_shippers_by_branch'),

    # ===== QUẢN LÝ NGƯỜI DÙNG =====
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/add/', views.user_add, name='user_add'),
    path('admin/users/edit/<int:id>/', views.user_edit, name='user_edit'),
    path('admin/users/delete/<int:id>/', views.user_delete, name='user_delete'),
    path('admin/users/detail/<int:id>/', views.user_detail, name='user_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
