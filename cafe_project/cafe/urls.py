from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
path('', views.home, name='home'),
path('user', views.user_home, name='user_home'),
path('menu/', views.user_menu, name='user_menu'),
path('cart/', views.cart, name='cart'),
path('order/create/', views.user_order_create, name='user_order_create'),


path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
#admin
path('admin/', views.admin_dashboard, name='admin_dashboard'),
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

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)