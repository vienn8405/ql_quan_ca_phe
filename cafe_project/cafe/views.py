from django.shortcuts import render, redirect, get_object_or_404
from cafe.models import User, Product, Order, Category, Inventory, Employee, OrderItem, RawMaterial, BranchMaterialStock, ProductRecipe, StockLog, CafeBranch, Table, Voucher, Attendance, Supplier, SupplierOrder, WorkShift, ShiftAssignment
from django.http import HttpResponse
from django.utils import timezone
from django.core.serializers import serialize
from cafe.models import CafeBranch
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib import messages
from django.db import models, transaction
from django.views.decorators.http import require_POST
from functools import wraps


# ==================== AUTH HELPERS ====================

def staff_login_required(view_func):
    """Decorator: yêu cầu đăng nhập (bất kỳ role staff nào)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Decorator: yêu cầu đăng nhập + đúng role.
    Ví dụ: @role_required('admin', 'cashier')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('login')
            user_role = request.session.get('user_role', '')
            if user_role not in allowed_roles:
                messages.error(request, '❌ Bạn không có quyền truy cập trang này')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ==================== VIEWS ====================

# Create your views here.
def home(request):
    products = Product.objects.filter(inventory__quantity__gt=0)

    return render(request, 'cafe/home.html', {
        'products': products
    })



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = User.objects.filter(
            username=username,
            password=password,
        ).first()

        if user:
            # Lưu session chung cho mọi role
            request.session['user_id'] = user.id
            request.session['user_role'] = user.role
            request.session['user_name'] = user.username

            # Tương thích ngược: admin + cashier giữ admin_id
            # để ~50 view cũ check admin_id vẫn hoạt động
            if user.role in ('admin', 'cashier'):
                request.session['admin_id'] = user.id
                return redirect('admin_dashboard')
            elif user.role == 'shipper':
                return redirect('shipper_deliveries')
            else:
                return redirect('home')
        else:
            messages.error(request, '❌ Sai tên đăng nhập hoặc mật khẩu')

    return render(request, 'cafe/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('home')



#quản lí chi nhánh
def branch_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    branches = CafeBranch.objects.all().order_by('id')
    return render(request, 'cafe/branch_list.html', {'branches': branches})


def branch_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        phone = request.POST.get('phone', '')
        open_time = request.POST.get('open_time', '')
        description = request.POST.get('description', '')
        delivery_radius = float(request.POST.get('delivery_radius', 3000))
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        latitude = float(request.POST['latitude'])
        longitude = float(request.POST['longitude'])

        CafeBranch.objects.create(
            name=name,
            address=address,
            phone=phone,
            open_time=open_time,
            description=description,
            delivery_radius=delivery_radius,
            is_active=is_active,
            image=image,
            location=Point(longitude, latitude)
        )
        return redirect('branch_list')

    return render(request, 'cafe/branch_add.html')


def branch_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    branch = get_object_or_404(CafeBranch, id=id)

    if request.method == 'POST':
        branch.name = request.POST['name']
        branch.address = request.POST['address']
        branch.phone = request.POST.get('phone', '')
        branch.open_time = request.POST.get('open_time', '')
        branch.description = request.POST.get('description', '')
        branch.delivery_radius = float(request.POST.get('delivery_radius', 3000))
        branch.is_active = request.POST.get('is_active') == 'on'

        image = request.FILES.get('image')
        if image:
            branch.image = image

        latitude = float(request.POST['latitude'])
        longitude = float(request.POST['longitude'])

        branch.location = Point(longitude, latitude)
        branch.save()
        return redirect('branch_list')

    return render(request, 'cafe/branch_edit.html', {
        'branch': branch,
        'latitude': branch.location.y if branch.location else '',
        'longitude': branch.location.x if branch.location else '',
    })

def branch_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    CafeBranch.objects.filter(id=id).delete()
    return redirect('branch_list')

#danh sách sản phẩm
def product_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    q = request.GET.get('q', '').strip()
    products = Product.objects.select_related('category').all().order_by('name')

    if q:
        search_filter = (
            models.Q(name__icontains=q) |
            models.Q(category__name__icontains=q)
        )

        raw_id = q.lstrip('#')
        if raw_id.isdigit():
            search_filter |= models.Q(id=int(raw_id))
            try:
                search_filter |= models.Q(price=float(raw_id))
            except ValueError:
                pass
        else:
            try:
                search_filter |= models.Q(price=float(q.replace(',', '').strip()))
            except ValueError:
                pass

        products = products.filter(search_filter).distinct()

    return render(request, 'cafe/product_list.html', {
        'products': products,
        'q': q,
    })


#thêm sản phẩm
def product_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')
    
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        category_id = request.POST['category']
        img = request.FILES.get('image')

        product = Product.objects.create(
            name=name,
            price=price,
            category=Category.objects.get(id=category_id),
            image=img
        )

        Inventory.objects.get_or_create(
            product=product,
            defaults={'quantity': 0}
        )

        return redirect('product_list')

    return render(request, 'cafe/product_add.html', {
        'categories': categories
    })

#xóa sản phẩm
def product_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    product = get_object_or_404(Product, id=id)

    if OrderItem.objects.filter(product=product).exists():
        messages.error(request, "❌ Không thể xóa sản phẩm vì đã tồn tại trong đơn hàng")
        return redirect('product_list')

    if ProductRecipe.objects.filter(product=product).exists():
        messages.error(request, "❌ Không thể xóa sản phẩm vì đang có công thức pha chế")
        return redirect('product_list')

    product.delete()
    messages.success(request, "✅ Đã xóa sản phẩm")
    return redirect('product_list')

#sửa sản phẩm 
def product_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    product = Product.objects.get(id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.category_id = request.POST['category']
         # nếu có upload ảnh mới thì thay ảnh
        img = request.FILES.get('image')
        if img:
            product.image = img
        product.save()
        return redirect('product_list')

    return render(request, 'cafe/product_edit.html', {
        'product': product,
        'categories': categories
    })


#danh sách đơn hàng
def order_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    q = request.GET.get('q', '').strip()
    orders = Order.objects.all().select_related('branch').prefetch_related('orderitem_set__product').order_by('-created_at')

    if q:
        normalized_q = q.lower()
        search_filter = (
            models.Q(customer_name__icontains=q) |
            models.Q(customer_phone__icontains=q) |
            models.Q(customer_address__icontains=q) |
            models.Q(branch__name__icontains=q) |
            models.Q(order_type__icontains=q) |
            models.Q(status__icontains=q) |
            models.Q(delivery_status__icontains=q) |
            models.Q(orderitem__product__name__icontains=q)
        )

        raw_id = q.lstrip('#')
        if raw_id.isdigit():
            search_filter |= models.Q(id=int(raw_id))

        order_type_aliases = {
            'mang ve': 'takeaway',
            'takeaway': 'takeaway',
            'giao hang': 'delivery',
            'delivery': 'delivery',
            'tai quan': 'dine_in',
            'tai cho': 'dine_in',
            'dine in': 'dine_in',
            'dine_in': 'dine_in',
        }
        status_aliases = {
            'cho xu ly': 'pending',
            'cho xac nhan': 'pending',
            'pending': 'pending',
            'xac nhan': 'confirmed',
            'confirmed': 'confirmed',
            'pha che': 'preparing',
            'dang pha che': 'preparing',
            'preparing': 'preparing',
            'dang giao': 'delivering',
            'delivering': 'delivering',
            'hoan tat': 'completed',
            'completed': 'completed',
            'huy': 'cancelled',
            'cancelled': 'cancelled',
        }

        if normalized_q in order_type_aliases:
            search_filter |= models.Q(order_type=order_type_aliases[normalized_q])
        if normalized_q in status_aliases:
            search_filter |= models.Q(status=status_aliases[normalized_q])

        orders = orders.filter(search_filter).distinct()

    return render(request, 'cafe/order_list.html', {
        'orders': orders,
        'q': q,
    })

#xem chi tiết đơn hàng (admin)
def admin_order_detail(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    order = get_object_or_404(Order, id=id)
    items = OrderItem.objects.filter(order=order).select_related('product')

    return render(request, 'cafe/admin_order_detail.html', {
        'order': order,
        'items': items,
    })

#Tạo đơn hàng
def order_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    products = Product.objects.filter(inventory__quantity__gt=0).select_related('inventory')

    if request.method == 'POST':
        product_id = request.POST['product']
        quantity = int(request.POST['quantity'])

        product = get_object_or_404(Product, id=product_id)
        inventory = get_object_or_404(Inventory, product=product)

        if inventory.quantity <= 0:
            return HttpResponse("❌ Sản phẩm đã hết hàng")

        if quantity > inventory.quantity:
            return HttpResponse(f"❌ Chỉ còn {inventory.quantity} sản phẩm trong kho")

        order = Order.objects.create(
            payment_method='cash',
            status='pending'
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        order.total_price = product.price * quantity
        order.save()

        inventory.quantity -= quantity
        inventory.save()

        return redirect('order_list')

    return render(request, 'cafe/order_add.html', {
        'products': products
    })


#Xóa đơn hàng
def order_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    order = get_object_or_404(Order, id=id)
    items = OrderItem.objects.filter(order=order)

    for item in items:
        inventory = get_object_or_404(Inventory, product=item.product)
        inventory.quantity += item.quantity
        inventory.save()

    order.delete()
    return redirect('order_list')

 #sửa đơn hàng
def order_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    order = get_object_or_404(Order, id=id)
    item = get_object_or_404(OrderItem, order=order)

    if order.status in ['completed', 'cancelled']:
        return redirect('order_list')

    products = Product.objects.filter(inventory__quantity__gt=0) | Product.objects.filter(id=item.product.id)

    if request.method == 'POST':
        product_id = request.POST['product']

        try:
            quantity = int(request.POST['quantity'])
        except ValueError:
            return HttpResponse("❌ Số lượng không hợp lệ")

        if quantity <= 0:
            return HttpResponse("❌ Số lượng phải lớn hơn 0")

        new_product = get_object_or_404(Product, id=product_id)
        old_product = item.product
        old_quantity = item.quantity

        # Trường hợp giữ nguyên sản phẩm, chỉ đổi số lượng
        if new_product.id == old_product.id:
            inventory = get_object_or_404(Inventory, product=old_product)

            available_stock = inventory.quantity + old_quantity

            if quantity > available_stock:
                return HttpResponse(f"❌ Chỉ còn {available_stock} sản phẩm trong kho")

            inventory.quantity = available_stock - quantity
            inventory.save()

        # Trường hợp đổi sang sản phẩm khác
        else:
            old_inventory = get_object_or_404(Inventory, product=old_product)
            new_inventory = get_object_or_404(Inventory, product=new_product)

            # hoàn lại kho sản phẩm cũ
            old_inventory.quantity += old_quantity
            old_inventory.save()

            # kiểm tra kho sản phẩm mới
            if new_inventory.quantity <= 0:
                return HttpResponse("❌ Sản phẩm mới đã hết hàng")

            if quantity > new_inventory.quantity:
                return HttpResponse(f"❌ Chỉ còn {new_inventory.quantity} sản phẩm trong kho")

            # trừ kho sản phẩm mới
            new_inventory.quantity -= quantity
            new_inventory.save()

        item.product = new_product
        item.quantity = quantity
        item.price = new_product.price
        item.save()

        order.total_price = item.price * item.quantity
        order.save()

        return redirect('order_list')

    return render(request, 'cafe/order_edit.html', {
        'order': order,
        'item': item,
        'products': products.distinct()
    })

#danh sách loại
def category_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    categories = Category.objects.all()
    return render(request, 'cafe/category_list.html', {
        'categories': categories
    })

#thêm loại
def category_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        name = request.POST['name']
        Category.objects.create(name=name)
        return redirect('category_list')

    return render(request, 'cafe/category_add.html')

#sửa loại
def category_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    category = Category.objects.get(id=id)

    if request.method == 'POST':
        category.name = request.POST['name']
        category.save()
        return redirect('category_list')

    return render(request, 'cafe/category_edit.html', {
        'category': category
    })


#xóa loại
def category_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    category = Category.objects.get(id=id)

    # Kiểm tra có sản phẩm đang dùng loại này không
    if category.product_set.exists():
        return HttpResponse(
            "Không thể xoá loại đang có sản phẩm!"
        )

    category.delete()
    return redirect('category_list')


#danh sách kho
def inventory_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    products = Product.objects.all()

    for product in products:
        Inventory.objects.get_or_create(
            product=product,
            defaults={'quantity': 0}
        )

    inventories = Inventory.objects.select_related('product', 'product__category').all().order_by('product__name')

    return render(request, 'cafe/inventory_list.html', {
        'inventories': inventories
    })

#nhập / xuất kho
def inventory_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    inventory = get_object_or_404(Inventory, id=id)
    error = None

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
        except ValueError:
            error = "Số lượng không hợp lệ"
            return render(request, 'cafe/inventory_edit.html', {
                'inventory': inventory,
                'error': error
            })

        if quantity < 0:
            error = "Số lượng tồn kho không được nhỏ hơn 0"
            return render(request, 'cafe/inventory_edit.html', {
                'inventory': inventory,
                'error': error
            })

        old_quantity = inventory.quantity
        inventory.quantity = quantity
        inventory.save()

        change_qty = quantity - old_quantity

        if change_qty != 0:
            StockLog.objects.create(
                stock_type='finished',
                action='import' if change_qty > 0 else 'export',
                product=inventory.product,
                quantity=change_qty,
                note='Admin điều chỉnh kho thành phẩm'
            )

        return redirect('inventory_list')

    return render(request, 'cafe/inventory_edit.html', {
        'inventory': inventory,
        'error': error
    })

#danh sách nhân viên
def employee_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    employees = Employee.objects.all()
    return render(request, 'cafe/employee_list.html', {
        'employees': employees
    })

#thêm nhân viên
def employee_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        Employee.objects.create(
            name=request.POST['name'],
            role=request.POST['role'],
            phone=request.POST['phone'],
            salary=request.POST['salary']
        )
        return redirect('employee_list')

    return render(request, 'cafe/employee_add.html')

#sửa nhân viên
def employee_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    employee = Employee.objects.get(id=id)

    if request.method == 'POST':
        employee.name = request.POST['name']
        employee.role = request.POST['role']
        employee.phone = request.POST['phone']
        employee.salary = request.POST['salary']
        employee.save()
        return redirect('employee_list')

    return render(request, 'cafe/employee_edit.html', {
        'employee': employee
    })

#xóa nhân viên
def employee_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    employee = Employee.objects.get(id=id)
    employee.delete()
    return redirect('employee_list')


#người dùng
def user_home(request):
    categories = Category.objects.all()
    return render(request, 'cafe/user_home.html', {
        'categories': categories
    })
#menu
def user_menu(request):
    products = Product.objects.select_related('category').all()

    product_data = []

    for p in products:
        inventory = Inventory.objects.filter(product=p).first()
        finished_qty = inventory.quantity if inventory else 0

        can_make, _ = can_make_product(p, 1)

        if finished_qty > 0:
            stock_status = "available"
            stock_text = "Có sẵn"
        elif can_make:
            stock_status = "makeable"
            stock_text = "Có thể pha chế"
        else:
            stock_status = "out"
            stock_text = "Tạm hết món"

        product_data.append({
            'product': p,
            'finished_qty': finished_qty,
            'stock_status': stock_status,
            'stock_text': stock_text,
        })

    return render(request, 'cafe/user_menu.html', {
        'product_data': product_data
    })
#xem giỏ hàng
def cart(request):
    cart = request.session.get('cart', {})

    total = 0
    for item in cart.values():
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']

    reservation_id = request.session.get('reservation_id')
    reservation = None
    if reservation_id:
        from .models import Reservation
        reservation = Reservation.objects.filter(id=reservation_id).first()

    branches = CafeBranch.objects.filter(is_active=True).order_by('name')

    return render(request, 'cafe/cart.html', {
        'cart': cart,
        'total': total,
        'branches': branches,
        'reservation': reservation,
    })



@require_POST
def user_order_create(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, "❌ Giỏ hàng đang trống")
        return redirect('cart')

    reservation_id = request.session.get('reservation_id')
    reservation = None
    if reservation_id:
        from .models import Reservation
        reservation = Reservation.objects.filter(id=reservation_id).first()

    payment_method = request.POST.get('payment_method', 'cash')
    
    if reservation:
        customer_name = reservation.customer_name
        customer_phone = reservation.customer_phone
        customer_email = reservation.customer_email or ''
        customer_address = ''
        note = request.POST.get('note', '').strip()
        order_type = 'dine_in'
        branch = reservation.branch
        customer_lat = None
        customer_lng = None
        delivery_distance = 0
        delivery_fee = 0
        delivery_status = 'not_required'
    else:
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        note = request.POST.get('note', '').strip()

        order_type = request.POST.get('order_type', 'takeaway')

        customer_lat_raw = request.POST.get('customer_lat', '').strip()
        customer_lng_raw = request.POST.get('customer_lng', '').strip()

        customer_lat = None
        customer_lng = None
        branch = None
        delivery_distance = 0
        delivery_fee = 0
        delivery_status = 'not_required'

        if order_type == 'delivery':
            if not customer_address:
                messages.error(request, "❌ Đơn giao hàng phải có địa chỉ giao")
                return redirect('cart')

            if not customer_lat_raw or not customer_lng_raw:
                messages.error(request, "❌ Vui lòng chọn vị trí giao hàng trên bản đồ hoặc lấy tọa độ")
                return redirect('cart')

            try:
                customer_lat = float(customer_lat_raw)
                customer_lng = float(customer_lng_raw)
            except ValueError:
                messages.error(request, "❌ Tọa độ giao hàng không hợp lệ")
                return redirect('cart')

            manual_branch_id = request.POST.get('selected_delivery_branch_id', '').strip()

            if manual_branch_id:
                try:
                    chosen_branch = CafeBranch.objects.get(id=manual_branch_id, is_active=True)
                except CafeBranch.DoesNotExist:
                    messages.error(request, "❌ Chi nhánh được chọn không tồn tại hoặc đã tạm nghỉ.")
                    return redirect('cart')

                from django.contrib.gis.geos import Point
                from django.contrib.gis.db.models.functions import Distance
                
                user_point = Point(customer_lng, customer_lat, srid=4326)
                branch_with_dist = CafeBranch.objects.filter(id=chosen_branch.id).annotate(
                    distance=Distance("location", user_point)
                ).first()

                if not branch_with_dist or not branch_with_dist.distance:
                    messages.error(request, "❌ Lỗi hệ thống: Không thể tính khoảng cách tới chi nhánh.")
                    return redirect('cart')

                dist_m = float(branch_with_dist.distance.m)

                if dist_m > float(chosen_branch.delivery_radius):
                    messages.error(
                        request, 
                        f"❌ Chi nhánh {chosen_branch.name} chỉ giao tối đa {chosen_branch.delivery_radius}m "
                        f"(điểm giao cách {dist_m:.0f}m). Vui lòng chọn quán gần hơn hoặc bật chế độ tự động."
                    )
                    return redirect('cart')

                branch = chosen_branch
                delivery_distance = float(f"{dist_m:.1f}")
                branch_reason = "Chọn thủ công từ bản đồ"
            else:
                result = find_optimal_branch(customer_lat, customer_lng)

                if not result:
                    messages.error(request, "❌ Không có chi nhánh nào giao được tới vị trí này")
                    return redirect('cart')

                branch = result['branch']
                delivery_distance = result['distance']
                branch_reason = result.get('reason', '')

            if delivery_distance <= 1000:
                delivery_fee = 10000
            elif delivery_distance <= 3000:
                delivery_fee = 15000
            else:
                delivery_fee = 20000

            delivery_status = 'waiting'

            # Thông báo cho khách biết chi nhánh phục vụ
            messages.info(
                request,
                f"🏬 Chi nhánh phục vụ: {branch.name} "
                f"({delivery_distance:.0f}m) — {branch_reason}"
            )

        else:
            # đơn tại quán / mang đi: có thể cho chọn chi nhánh thủ công nếu muốn
            branch_id = request.POST.get('branch_id')
            if branch_id:
                branch = CafeBranch.objects.filter(id=branch_id, is_active=True).first()

    # Xử lý voucher từ giỏ hàng
    voucher_code = request.POST.get('voucher_code', '').strip().upper()
    discount_amount = 0
    applied_voucher = None

    if voucher_code:
        try:
            applied_voucher = Voucher.objects.get(code=voucher_code, is_active=True)
        except Voucher.DoesNotExist:
            applied_voucher = None

    ok, error = validate_cart_stock(cart, branch=branch)
    if not ok:
        messages.error(request, f"❌ {error}")
        return redirect('cart')

    try:
        reservation_id = request.session.get('reservation_id')

        with transaction.atomic():
            if reservation_id:
                order_type = 'dine_in'

            order = Order.objects.create(
                total_price=0,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email or None,
                customer_address=customer_address,
                note=note,
                payment_method=payment_method,
                status='pending',
                order_type=order_type,
                delivery_status=delivery_status,
                delivery_fee=delivery_fee,
                delivery_distance=delivery_distance or 0,
                branch=branch,
                customer_lat=customer_lat,
                customer_lng=customer_lng,
            )

            total = 0

            for pid, item in cart.items():
                product = get_object_or_404(Product, id=pid)
                quantity = item['quantity']
                price = item['price']

                ok, error = process_product_order(product, quantity, branch=branch)
                if not ok:
                    raise ValueError(f"{product.name}: {error}")

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )

                total += price * quantity

            # Áp dụng voucher nếu hợp lệ
            if applied_voucher is not None:
                is_valid, _ = applied_voucher.is_valid(total)  # type: ignore
                if is_valid:
                    discount_amount = applied_voucher.calc_discount(total)  # type: ignore
                    applied_voucher.used_count += 1  # type: ignore
                    applied_voucher.save()  # type: ignore
                    order.voucher = applied_voucher
                    order.discount_amount = discount_amount

            order.total_price = max(0, total + delivery_fee - discount_amount)
            order.save()

            if reservation_id:
                from .models import Reservation
                reservation = Reservation.objects.filter(id=reservation_id).first()
                if reservation:
                    reservation.order = order
                    reservation.deposit_amount = int(order.total_price * 0.3)
                    reservation.save()

    except Exception as e:
        messages.error(request, f"❌ Không thể tạo đơn: {e}")
        return redirect('cart')

    request.session["order_id"] = order.id
    request.session['cart'] = {}
    if 'reservation_id' in request.session:
        del request.session['reservation_id']
    request.session.modified = True

    # Gửi email xác nhận đơn hàng
    from .services.email_service import send_order_confirmation_email
    send_order_confirmation_email(order)

    messages.success(request, "✅ Đặt hàng thành công")
    return redirect('user_order_detail')

#thêm vào giỏ
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    inventory = get_object_or_404(Inventory, product=product)

    cart = request.session.get('cart', {})
    pid = str(product_id)

    current_qty = cart.get(pid, {}).get('quantity', 0)
    desired_qty = current_qty + 1

    if desired_qty > inventory.quantity:
        missing_qty = desired_qty - inventory.quantity
        can_make, error = can_make_product(product, missing_qty)

        if not can_make:
            messages.error(request, f"❌ {product.name}: {error}")
            return redirect('user_menu')

    image_url = product.image.url if product.image else ""

    if pid in cart:
        cart[pid]['quantity'] += 1
        cart[pid]['image'] = image_url
        cart[pid]['name'] = product.name
        cart[pid]['price'] = int(product.price)
    else:
        cart[pid] = {
            'name': product.name,
            'price': int(product.price),
            'quantity': 1,
            'image': image_url,
        }

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"✅ Đã thêm {product.name} vào giỏ hàng")
    return redirect('user_menu')
#thêm hoặc giảm số lượng sản phẩm
def cart_update(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)

    if pid not in cart:
        return redirect('cart')

    product = get_object_or_404(Product, id=product_id)
    inventory = get_object_or_404(Inventory, product=product)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity < 1:
            quantity = 1

        if quantity > inventory.quantity:
            missing_qty = quantity - inventory.quantity
            can_make, error = can_make_product(product, missing_qty)

            if not can_make:
                messages.error(request, f"❌ {product.name}: {error}")
                return redirect('cart')

        cart[pid]['quantity'] = quantity
        request.session['cart'] = cart
        request.session.modified = True

        messages.success(request, f"✅ Đã cập nhật số lượng {product.name}")

    return redirect('cart')

#xóa sản phẩm khỏi giỏ
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)

    if pid in cart:
        product_name = cart[pid]['name']
        del cart[pid]
        messages.info(request, f"🗑️ Đã xóa {product_name} khỏi giỏ hàng")

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')

#view xem đon hàng
def user_order_detail(request):
    order_id = request.session.get('order_id')

    if not order_id:
        return render(request, 'cafe/order_empty.html')

    order = Order.objects.filter(id=order_id).first()

    if not order:
        request.session.pop('order_id', None)
        return render(request, 'cafe/order_empty.html')

    reservation = None
    try:
        reservation = order.reservation
    except Exception:
        pass

    items = OrderItem.objects.filter(order=order)

    return render(request, "cafe/order_detail.html", {
        "order": order,
        "items": items,
        "reservation": reservation,
    })
#tool1 view bản đồ


def map_view(request):
    branches = CafeBranch.objects.all()
    return render(request, "cafe/map.html", {
        "branches": branches
    })
#tool1 Trả về danh sách chi nhánh dạng GeoJSON tự tạo
def branches_geojson(request):
    branches = CafeBranch.objects.filter(is_active=True)

    features = []

    for branch in branches:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [branch.location.x, branch.location.y]
            },
            "properties": {
                "id": branch.id,
                "name": branch.name,
                "address": branch.address,
                "phone": branch.phone,
                "open_time": branch.open_time,
                "description": branch.description,
                "delivery_radius": branch.delivery_radius,
                "is_active": branch.is_active,
                "image": branch.image.url if branch.image else ""
            }
        })

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })


#tool2 tìm quán gần nhất
def cafes_near_me(request):

    # Kiểm tra tham số gửi lên có hợp lệ không
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
        radius = float(request.GET.get("radius", 1000))  # mét
    except (TypeError, ValueError):
        return JsonResponse({"error": "Sai tham số"}, status=400)

    # Tạo điểm vị trí người dùng
    user_point = Point(lng, lat, srid=4326)

    # Annotate thêm khoảng cách
    cafes = CafeBranch.objects.annotate(
        distance=Distance("location", user_point)
    ).filter(
        location__distance_lte=(user_point, D(m=radius))
    ).order_by("distance")

    result = []

    for cafe in cafes:
        result.append({
            "id": cafe.id,
            "name": cafe.name,
            "address": cafe.address,
            "phone": cafe.phone,
            "lat": cafe.location.y,
            "lng": cafe.location.x,
            "distance": round(cafe.distance.m, 1),
            "delivery_radius": cafe.delivery_radius,
        })

    return JsonResponse(result, safe=False)


def api_branch_stats(request):
    """API thống kê từng chi nhánh: số bàn trống, đơn hôm nay, doanh thu tháng"""
    from .models import CafeBranch, Table, Order
    from django.utils import timezone
    from django.db.models import Sum

    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    branches = CafeBranch.objects.filter(is_active=True)
    result = {}

    for branch in branches:
        tables_total = Table.objects.filter(branch=branch).count()
        tables_available = Table.objects.filter(branch=branch, status='available').count()
        tables_occupied = Table.objects.filter(branch=branch, status='occupied').count()
        tables_reserved = Table.objects.filter(branch=branch, status='reserved').count()

        orders_today = Order.objects.filter(
            branch=branch,
            created_at__date=today,
            status__in=['completed', 'confirmed', 'preparing', 'delivering']
        ).count()

        revenue_month = Order.objects.filter(
            branch=branch,
            created_at__date__gte=this_month_start,
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0

        result[branch.id] = {
            'name': branch.name,
            'tables_total': tables_total,
            'tables_available': tables_available,
            'tables_occupied': tables_occupied,
            'tables_reserved': tables_reserved,
            'orders_today': orders_today,
            'revenue_month': revenue_month,
        }

    return JsonResponse(result)


def sync_raw_material_total(material):
    branch_stocks = material.branch_stocks.all()
    if branch_stocks.exists():
        material.quantity = sum(stock.quantity for stock in branch_stocks)
        material.min_quantity = sum(stock.min_quantity for stock in branch_stocks)
        material.save(update_fields=['quantity', 'min_quantity', 'updated_at'])


def get_branch_material_stock(material, branch, create=False):
    if not branch:
        return None

    stock = material.branch_stocks.filter(branch=branch).first()
    if stock or not create:
        return stock

    has_any_branch_stock = material.branch_stocks.exists()
    stock = BranchMaterialStock.objects.create(
        material=material,
        branch=branch,
        quantity=material.quantity if not has_any_branch_stock else 0,
        min_quantity=material.min_quantity,
    )
    sync_raw_material_total(material)
    return stock


def get_material_quantity(material, branch=None):
    if branch:
        if material.branch_stocks.exists():
            stock = material.branch_stocks.filter(branch=branch).first()
            return stock.quantity if stock else 0
        return material.quantity

    if material.branch_stocks.exists():
        return sum(stock.quantity for stock in material.branch_stocks.all())
    return material.quantity


def get_material_min_quantity(material, branch=None):
    if branch:
        if material.branch_stocks.exists():
            stock = material.branch_stocks.filter(branch=branch).first()
            return stock.min_quantity if stock else material.min_quantity
        return material.min_quantity

    if material.branch_stocks.exists():
        return sum(stock.min_quantity for stock in material.branch_stocks.all())
    return material.min_quantity


def can_make_product(product, quantity_needed=1, branch=None):
    recipes = ProductRecipe.objects.filter(product=product).select_related('material')

    if not recipes.exists():
        return False, "Món này chưa có công thức pha chế"

    for recipe in recipes:
        required = recipe.quantity_required * quantity_needed
        available_qty = get_material_quantity(recipe.material, branch)
        if available_qty < required:
            branch_text = f" tại chi nhánh {branch.name}" if branch else ""
            return False, f"Không đủ nguyên liệu{branch_text}: {recipe.material.name}"

    return True, ""

def consume_materials_for_product(product, quantity_needed=1, branch=None):
    recipes = ProductRecipe.objects.filter(product=product).select_related('material')

    for recipe in recipes:
        required = recipe.quantity_required * quantity_needed
        material = RawMaterial.objects.select_for_update().get(id=recipe.material.id)

        branch_stock = None
        if branch and material.branch_stocks.exists():
            branch_stock = BranchMaterialStock.objects.select_for_update().filter(
                material=material,
                branch=branch,
            ).first()
            if not branch_stock or branch_stock.quantity < required:
                raise ValueError(f"Không đủ nguyên liệu tại chi nhánh {branch.name}: {material.name}")

            branch_stock.quantity -= required
            branch_stock.save(update_fields=['quantity', 'updated_at'])
            sync_raw_material_total(material)
        else:
            if material.quantity < required:
                raise ValueError(f"Không đủ nguyên liệu: {material.name}")

            material.quantity -= required
            material.save()

        StockLog.objects.create(
            stock_type='material',
            action='make',
            product=product,
            material=material,
            branch=branch,
            quantity=-required,
            note=f'Trừ nguyên liệu để pha {quantity_needed} {product.name}'
        )

def process_product_order(product, quantity, branch=None):
    inventory, _ = Inventory.objects.select_for_update().get_or_create(
        product=product,
        defaults={'quantity': 0}
    )

    # Nếu đủ thành phẩm
    if inventory.quantity >= quantity:
        inventory.quantity -= quantity
        inventory.save()

        StockLog.objects.create(
            stock_type='finished',
            action='order',
            product=product,
            branch=branch,
            quantity=-quantity,
            note='Bán từ kho thành phẩm'
        )
        return True, ""

    # Nếu thiếu thành phẩm, thử pha từ nguyên liệu
    missing_qty = quantity - inventory.quantity
    can_make, error = can_make_product(product, missing_qty, branch=branch)
    if not can_make:
        return False, error

    sold_finished = inventory.quantity
    inventory.quantity = 0
    inventory.save()

    if sold_finished > 0:
        StockLog.objects.create(
            stock_type='finished',
            action='order',
            product=product,
            branch=branch,
            quantity=-sold_finished,
            note='Bán phần thành phẩm còn lại'
        )

    consume_materials_for_product(product, missing_qty, branch=branch)

    StockLog.objects.create(
        stock_type='finished',
        action='make',
        product=product,
        branch=branch,
        quantity=missing_qty,
        note='Pha chế tự động từ nguyên liệu'
    )

    return True, ""

def material_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    branch_id = request.GET.get('branch_id', '').strip()
    selected_branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')
    materials = RawMaterial.objects.all().prefetch_related('branch_stocks__branch').order_by('name')

    for material in materials:
        material.display_quantity = get_material_quantity(material, selected_branch)
        material.display_min_quantity = get_material_min_quantity(material, selected_branch)

    return render(request, 'cafe/material_list.html', {
        'materials': materials,
        'branches': branches,
        'selected_branch': selected_branch,
    })

def material_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    branches = CafeBranch.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        quantity = float(request.POST['quantity'])
        min_quantity = float(request.POST.get('min_quantity', 0))
        material = RawMaterial.objects.create(
            name=request.POST['name'],
            unit=request.POST['unit'],
            quantity=quantity,
            min_quantity=min_quantity
        )

        if branch_id:
            branch = get_object_or_404(CafeBranch, id=branch_id)
            BranchMaterialStock.objects.create(
                material=material,
                branch=branch,
                quantity=quantity,
                min_quantity=min_quantity,
            )
            sync_raw_material_total(material)
            StockLog.objects.create(
                stock_type='material',
                action='import',
                material=material,
                branch=branch,
                quantity=quantity,
                note='Tạo mới nguyên liệu và nhập kho theo chi nhánh'
            )
        else:
            StockLog.objects.create(
                stock_type='material',
                action='import',
                material=material,
                quantity=quantity,
                note='Tạo mới nguyên liệu (dữ liệu dùng chung cũ)'
            )
        if branch_id:
            return redirect(f"{reverse('material_list')}?branch_id={branch_id}")
        return redirect('material_list')

    return render(request, 'cafe/material_add.html', {'branches': branches})

def material_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    material = get_object_or_404(RawMaterial, id=id)
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')
    branch_id = request.GET.get('branch_id') or request.POST.get('branch_id')
    selected_branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

    if request.method == 'POST':
        try:
            material.name = request.POST['name']
            material.unit = request.POST['unit']
            new_quantity = float(request.POST['quantity'])
            new_min_quantity = float(request.POST.get('min_quantity', 0))
            material.save()

            change_qty = 0

            if selected_branch:
                stock = get_branch_material_stock(material, selected_branch, create=True)
                old_quantity = float(stock.quantity) if stock else 0
                if stock:
                    stock.quantity = new_quantity
                    stock.min_quantity = new_min_quantity
                    stock.save()
                sync_raw_material_total(material)
                change_qty = new_quantity - old_quantity
            else:
                old_quantity = float(material.quantity)
                material.quantity = new_quantity
                material.min_quantity = new_min_quantity
                material.save()
                change_qty = new_quantity - old_quantity

            if change_qty != 0:
                StockLog.objects.create(
                    stock_type='material',
                    action='import' if change_qty > 0 else 'export',
                    material=material,
                    branch=selected_branch,
                    quantity=change_qty,
                    note='Admin điều chỉnh số lượng nguyên liệu theo chi nhánh' if selected_branch else 'Admin điều chỉnh số lượng nguyên liệu'
                )

            if selected_branch:
                return redirect(f"{reverse('material_list')}?branch_id={selected_branch.id}")
            return redirect('material_list')

        except ValueError:
            return HttpResponse("❌ Số lượng nguyên liệu không hợp lệ")

    return render(request, 'cafe/material_edit.html', {
        'material': material,
        'branches': branches,
        'selected_branch': selected_branch,
        'display_quantity': get_material_quantity(material, selected_branch),
        'display_min_quantity': get_material_min_quantity(material, selected_branch),
    })

def recipe_manage(request, product_id):
    if 'admin_id' not in request.session:
        return redirect('login')

    product = Product.objects.get(id=product_id)
    recipes = ProductRecipe.objects.filter(product=product)
    materials = RawMaterial.objects.all()
    error = None

    if request.method == 'POST':
        material_id = request.POST.get('material')
        quantity_required = request.POST.get('quantity_required')

        if not material_id or not quantity_required:
            error = "Vui lòng chọn nguyên liệu và nhập số lượng cần dùng."
        else:
            material = RawMaterial.objects.get(id=material_id)

            # kiểm tra nguyên liệu đã tồn tại trong công thức chưa
            existed = ProductRecipe.objects.filter(
                product=product,
                material=material
            ).first()

            if existed:
                error = "Nguyên liệu này đã có trong công thức."
            else:
                ProductRecipe.objects.create(
                    product=product,
                    material=material,
                    quantity_required=float(quantity_required)
                )
                return redirect('recipe_manage', product_id=product.id)

    return render(request, 'cafe/recipe_manage.html', {
        'product': product,
        'recipes': recipes,
        'materials': materials,
        'error': error
    })

def recipe_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    recipe = get_object_or_404(ProductRecipe, id=id)
    product_id = recipe.product.id
    recipe.delete()
    return redirect('recipe_manage', product_id=product_id)


def inventory_make(request, product_id):
    if 'admin_id' not in request.session:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')
    inventory, created = Inventory.objects.get_or_create(
    product=product,
    defaults={'quantity': 0}
)

    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        branch_id = request.POST.get('branch_id')
        branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

        if qty < 1:
            qty = 1

        if not branch:
            messages.error(request, "❌ Vui lòng chọn chi nhánh để trừ kho nguyên liệu")
            return redirect('inventory_make', product_id=product.id)

        can_make, error = can_make_product(product, qty, branch=branch)
        if not can_make:
            messages.error(request, f"❌ {product.name}: {error}")
            return redirect('inventory_list')

        consume_materials_for_product(product, qty, branch=branch)
        inventory.quantity += qty
        inventory.save()

        StockLog.objects.create(
            stock_type='finished',
            action='make',
            product=product,
            branch=branch,
            quantity=qty,
            note=f'Pha chế thêm {qty} {product.name} từ nguyên liệu chi nhánh {branch.name}'
        )

        messages.success(request, f"✅ Đã pha chế thêm {qty} {product.name}")
        return redirect('inventory_list')

    return render(request, 'cafe/inventory_make.html', {
        'product': product,
        'inventory': inventory,
        'branches': branches,
    })

def restore_order_inventory(order):
    items = OrderItem.objects.select_related('product').filter(order=order)

    for item in items:
        inventory, _ = Inventory.objects.get_or_create(
            product=item.product,
            defaults={'quantity': 0}
        )
        inventory.quantity += item.quantity
        inventory.save()

        StockLog.objects.create(
            stock_type='finished',
            action='import',
            product=item.product,
            quantity=item.quantity,
            note=f'Hoàn kho do admin hủy đơn #{order.id}'
        )

def order_update_status(request, order_id, status):
    if 'admin_id' not in request.session:
        return redirect('login')

    order = get_object_or_404(Order, id=order_id)

    # Luồng trạng thái mới - KHÔNG cho phép ready_for_delivery -> delivering trực tiếp
    allowed_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['preparing', 'cancelled'],
        'preparing': ['ready_for_delivery', 'cancelled'],
        'ready_for_delivery': ['cancelled'],  # ⚠️ Chỉ shipper mới được phép set delivering
        'delivering': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': [],
    }

    if status not in allowed_transitions.get(order.status, []):
        messages.error(request, f"❌ Không thể chuyển từ '{order.get_status_display()}' sang '{status}'")
        return redirect('order_list')
        
    old_status = order.status

    with transaction.atomic():
        if status == 'cancelled' and order.status in ['pending', 'confirmed', 'preparing', 'ready_for_delivery', 'delivering']:
            restore_order_inventory(order)

        order.status = status

        if order.order_type == 'delivery':
            if status == 'confirmed':
                if order.delivery_status not in ['delivered', 'shipping', 'failed']:
                    order.delivery_status = 'assigned' if order.assigned_shipper else 'waiting'
            elif status == 'completed':
                order.delivery_status = 'delivered'
                order.delivered_at = timezone.now()
                order.failed_at = None
                order.failure_reason = ''
            elif status == 'cancelled':
                # Không set delivery_status = failed khi admin hủy đơn
                # Giữ nguyên trạng thái giao hàng hiện tại
                pass

        order.save()

        # Logic Tích điểm thành viên
        if status == 'completed' and order.customer_phone:
            from .models import CustomerProfile
            profile, _ = CustomerProfile.objects.get_or_create(
                phone=order.customer_phone,
                defaults={'name': order.customer_name}
            )
            profile.total_spent += order.total_price
            profile.points += int(order.total_price * 0.05)  # 5% tích điểm
            profile.update_rank()
            
    # Gửi email cập nhật trạng thái đơn hàng
    if old_status != status:
        from .services.email_service import send_order_status_update_email
        send_order_status_update_email(order, old_status=old_status)
        
    messages.success(request, "✅ Cập nhật trạng thái thành công")
    return redirect('order_list')

def order_mark_paid(request, order_id):
    if 'admin_id' not in request.session:
        return redirect('login')
    order = get_object_or_404(Order, id=order_id)
    if not order.is_paid:
        order.is_paid = True
        order.save()
        messages.success(request, f"✅ Đã xác nhận khách chuyển khoản cho Đơn #{order.id}")
    return redirect('admin_order_detail', id=order.id)

def stocklog_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    branch_id = request.GET.get('branch_id', '').strip()
    logs = StockLog.objects.select_related('product', 'material', 'branch').all().order_by('-created_at')
    if branch_id:
        logs = logs.filter(branch_id=branch_id)
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')
    return render(request, 'cafe/stocklog_list.html', {
        'logs': logs,
        'branches': branches,
        'selected_branch_id': branch_id,
    })

def material_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    material = get_object_or_404(RawMaterial, id=id)

    if ProductRecipe.objects.filter(material=material).exists():
        messages.error(request, "❌ Không thể xóa nguyên liệu vì đang được dùng trong công thức")
        return redirect('material_list')

    material.delete()
    messages.success(request, "✅ Đã xóa nguyên liệu")
    return redirect('material_list')

@require_POST
def cancel_order(request, order_id):
    session_order_id = request.session.get("order_id")

    if session_order_id != order_id:
        messages.error(request, "❌ Bạn không thể hủy đơn này")
        return redirect('user_order_detail')

    order = get_object_or_404(Order, id=order_id)

    if order.status != 'pending':
        messages.error(request, "❌ Chỉ được hủy đơn khi đang chờ xử lý")
        return redirect('user_order_detail')

    with transaction.atomic():
        items = OrderItem.objects.select_related('product').filter(order=order)

        for item in items:
            inventory, _ = Inventory.objects.select_for_update().get_or_create(
                product=item.product,
                defaults={'quantity': 0}
            )
            inventory.quantity += item.quantity
            inventory.save()

            StockLog.objects.create(
                stock_type='finished',
                action='import',
                product=item.product,
                quantity=item.quantity,
                note=f'Hoàn kho do hủy đơn #{order.id}'
            )

        order.status = 'cancelled'
        order.save()

    messages.success(request, "✅ Đã hủy đơn hàng")
    return redirect('user_order_detail')

#Hàm kiểm tra tổng nguyên liệu cho cả giỏ hàng
def validate_cart_stock(cart, branch=None):
    material_requirements: dict = {}

    for pid, item in cart.items():
        product = get_object_or_404(Product, id=pid)
        inventory, _ = Inventory.objects.get_or_create(
            product=product,
            defaults={'quantity': 0}
        )

        quantity = item['quantity']

        # nếu đủ kho thành phẩm thì không cần tính nguyên liệu
        if inventory.quantity >= quantity:
            continue

        missing_qty = quantity - inventory.quantity
        recipes = ProductRecipe.objects.filter(product=product).select_related('material')

        if not recipes.exists():
            return False, f"{product.name} chưa có công thức pha chế"

        for recipe in recipes:
            required = recipe.quantity_required * missing_qty
            material_id = recipe.material.id

            if material_id not in material_requirements:
                material_requirements[material_id] = {
                    'name': recipe.material.name,
                    'required': 0,
                }

            material_requirements[material_id]['required'] += required  # type: ignore

    for material_id, info in material_requirements.items():
        material = RawMaterial.objects.get(id=material_id)
        available_qty = get_material_quantity(material, branch)
        if available_qty < info['required']:  # type: ignore
            branch_text = f" tại chi nhánh {branch.name}" if branch else ""
            return False, f"Không đủ nguyên liệu{branch_text}: {info['name']}"  # type: ignore

    return True, ""

def find_nearest_branch(lat, lng):
    user_point = Point(lng, lat, srid=4326)

    branch = CafeBranch.objects.filter(is_active=True).annotate(
        distance=Distance("location", user_point)
    ).order_by("distance").first()

    return branch

def find_serving_branch(lat, lng):
    """Wrapper tương thích ngược — trả (branch, distance)"""
    result = find_optimal_branch(lat, lng)
    if result:
        return result['branch'], result['distance']
    return None, None


def find_optimal_branch(lat, lng):
    """Chọn chi nhánh tối ưu cho đơn giao hàng.
    Tiêu chí: trong vùng giao → ít tải nhất hôm nay → gần nhất.
    Trả dict: {branch, distance, reason, candidates} hoặc None.
    """
    user_point = Point(float(lng), float(lat), srid=4326)

    branches = CafeBranch.objects.filter(is_active=True).annotate(
        distance=Distance("location", user_point)
    ).order_by("distance")

    # Lọc chi nhánh trong vùng giao hàng
    candidates = []
    for b in branches:
        if not b.distance:
            continue
        dist_m = float(b.distance.m)
        if dist_m <= float(b.delivery_radius):
            candidates.append({
                'branch': b,
                'distance': float(f"{dist_m:.1f}"),
                'name': b.name,
            })

    if not candidates:
        return None

    # Nếu chỉ có 1 → chọn luôn
    if len(candidates) == 1:
        c = candidates[0]
        return {
            'branch': c['branch'],
            'distance': c['distance'],
            'reason': f"Chi nhánh duy nhất phục vụ vùng này",
            'candidates': candidates,
        }

    # Đếm đơn hôm nay mỗi chi nhánh (tải)
    today = timezone.now().date()
    for c in candidates:
        c['today_orders'] = Order.objects.filter(
            branch=c['branch'],
            created_at__date=today
        ).count()

    # Sắp xếp: Gần nhất → Ít tải nhất (Dùng tải để tie break nếu khoảng cách bằng nhau)
    candidates.sort(key=lambda x: (x['distance'], x['today_orders']))

    chosen = candidates[0]

    # Xác định lý do (Vì đã sort theo khoảng cách nên chosen luôn là gần nhất)
    # Nếu có 2 quán bằng khoảng cách, lý do sẽ hiển thị thêm ưu thế ít tải
    if len(candidates) > 1 and chosen['distance'] == candidates[1]['distance']:
        reason = f"Gần nhất ({chosen['distance']:.0f}m) và ít tải hơn ({chosen['today_orders']} đơn chạy hôm nay)"
    else:
        reason = f"Chi nhánh gần nhất ({chosen['distance']:.0f}m)"

    return {
        'branch': chosen['branch'],
        'distance': chosen['distance'],
        'reason': reason,
        'candidates': candidates,
    }


# ==================== QUẢN LÝ BÀN ====================

def table_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')
    
    from .models import CafeBranch
    branches = CafeBranch.objects.all()
    branch_id = request.GET.get('branch_id')

    if branch_id:
        tables = Table.objects.filter(branch_id=branch_id).order_by('number')
    else:
        tables = Table.objects.all().order_by('branch__name', 'number')
        
    return render(request, 'cafe/table_list.html', {
        'tables': tables,
        'branches': branches,
        'selected_branch': int(branch_id) if branch_id else None
    })


def table_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')
    
    from .models import CafeBranch
    branches = CafeBranch.objects.all()

    if request.method == 'POST':
        Table.objects.create(
            number=request.POST['number'],
            area=request.POST.get('area', ''),
            capacity=int(request.POST.get('capacity', 4)),
            status=request.POST.get('status', 'available'),
            branch_id=request.POST.get('branch')
        )
        messages.success(request, '✅ Đã thêm bàn mới')
        return redirect('table_list')
    return render(request, 'cafe/table_add.html', {'branches': branches})


def table_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')
    table = get_object_or_404(Table, id=id)
    from .models import CafeBranch
    branches = CafeBranch.objects.all()

    if request.method == 'POST':
        table.number = request.POST['number']
        table.area = request.POST.get('area', '')
        table.capacity = int(request.POST.get('capacity', 4))
        table.status = request.POST.get('status', 'available')
        table.branch_id = request.POST.get('branch')
        table.save()
        messages.success(request, '✅ Đã cập nhật bàn')
        return redirect('table_list')
    return render(request, 'cafe/table_edit.html', {'table': table, 'branches': branches})


def table_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')
    table = get_object_or_404(Table, id=id)
    if Order.objects.filter(table=table, status__in=['pending', 'confirmed', 'preparing']).exists():
        messages.error(request, '❌ Không thể xóa bàn đang có đơn hàng đang xử lý')
        return redirect('table_list')
    table.delete()
    messages.success(request, '✅ Đã xóa bàn')
    return redirect('table_list')


# ==================== VOUCHER / KHUYẾN MÃI ====================

def voucher_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')
    vouchers = Voucher.objects.all().order_by('-created_at')
    return render(request, 'cafe/voucher_list.html', {'vouchers': vouchers})


def voucher_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')
    
    from .models import CafeBranch
    branches = CafeBranch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        expired_raw = request.POST.get('expired_at', '').strip()
        expired_at = None
        if expired_raw:
            from django.utils.dateparse import parse_datetime
            expired_at = parse_datetime(expired_raw)
            
        branch_id = request.POST.get('branch_id')
        branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

        Voucher.objects.create(
            code=request.POST['code'].strip().upper(),
            description=request.POST.get('description', ''),
            discount_type=request.POST.get('discount_type', 'percent'),
            discount_value=int(request.POST.get('discount_value', 0)),
            min_order_value=int(request.POST.get('min_order_value', 0)),
            max_uses=int(request.POST.get('max_uses', 100)),
            expired_at=expired_at,
            is_active=request.POST.get('is_active') == 'on',
            branch=branch,
        )
        messages.success(request, '✅ Đã thêm voucher')
        return redirect('voucher_list')
    return render(request, 'cafe/voucher_add.html', {'branches': branches})


def voucher_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')
    voucher = get_object_or_404(Voucher, id=id)
    
    from .models import CafeBranch
    branches = CafeBranch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        expired_raw = request.POST.get('expired_at', '').strip()
        expired_at = None
        if expired_raw:
            from django.utils.dateparse import parse_datetime
            expired_at = parse_datetime(expired_raw)
            
        branch_id = request.POST.get('branch_id')
        branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

        voucher.code = request.POST['code'].strip().upper()
        voucher.description = request.POST.get('description', '')
        voucher.discount_type = request.POST.get('discount_type', 'percent')
        voucher.discount_value = int(request.POST.get('discount_value', 0))
        voucher.min_order_value = int(request.POST.get('min_order_value', 0))
        voucher.max_uses = int(request.POST.get('max_uses', 100))
        voucher.expired_at = expired_at
        voucher.is_active = request.POST.get('is_active') == 'on'
        voucher.branch = branch
        voucher.save()
        messages.success(request, '✅ Đã cập nhật voucher')
        return redirect('voucher_list')
    return render(request, 'cafe/voucher_edit.html', {'voucher': voucher, 'branches': branches})


def voucher_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')
    voucher = get_object_or_404(Voucher, id=id)
    voucher.delete()
    messages.success(request, '✅ Đã xóa voucher')
    return redirect('voucher_list')


def apply_voucher(request):
    """API AJAX: kiểm tra và tính số tiền giảm của voucher"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    code = request.POST.get('code', '').strip().upper()
    try:
        order_total = int(request.POST.get('order_total', 0))
    except ValueError:
        return JsonResponse({'error': 'Tổng tiền không hợp lệ'}, status=400)

    try:
        voucher = Voucher.objects.get(code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Mã voucher không tồn tại'})

    branch_id = request.POST.get('branch_id')
    valid, msg = voucher.is_valid(order_total, branch_id)
    if not valid:
        return JsonResponse({'valid': False, 'error': msg})

    discount = voucher.calc_discount(order_total)
    return JsonResponse({
        'valid': True,
        'code': voucher.code,
        'discount': discount,
        'description': voucher.description,
        'final_total': order_total - discount,
    })


# ==================== CHẤM CÔNG NHÂN VIÊN ====================

def attendance_list(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    from datetime import date as dt_date
    import calendar

    # Lấy tháng/năm từ query param hoặc tháng hiện tại
    today = dt_date.today()
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except ValueError:
        month, year = today.month, today.year

    employee_id = request.GET.get('employee_id', '')

    logs = Attendance.objects.filter(date__year=year, date__month=month).select_related('employee').order_by('-date', 'employee__name')

    if employee_id:
        logs = logs.filter(employee_id=employee_id)

    employees = Employee.objects.all().order_by('name')

    # Tổng hợp số ngày công theo nhân viên (employee_id -> days worked)
    summary = {}
    for log in logs:
        eid = log.employee.id
        if eid not in summary:
            summary[eid] = {'name': log.employee.name, 'days': 0, 'hours': 0.0}
        summary[eid]['days'] += 1
        summary[eid]['hours'] += log.work_hours

    return render(request, 'cafe/attendance_list.html', {
        'logs': logs,
        'employees': employees,
        'selected_employee_id': employee_id,
        'month': month,
        'year': year,
        'summary': summary.values(),
        'months': list(range(1, 13)),
        'years': list(range(today.year - 2, today.year + 1)),
    })


def attendance_edit(request, employee_id):
    if 'admin_id' not in request.session:
        return redirect('login')

    from datetime import date as dt_date
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        check_in_str = request.POST.get('check_in', '').strip()
        check_out_str = request.POST.get('check_out', '').strip()
        note = request.POST.get('note', '').strip()

        from django.utils.dateparse import parse_date, parse_time
        date = parse_date(date_str)
        if not date:
            messages.error(request, '❌ Ngày không hợp lệ')
            return redirect('attendance_list')

        check_in = parse_time(check_in_str) if check_in_str else None
        check_out = parse_time(check_out_str) if check_out_str else None

        attendance, created = Attendance.objects.get_or_create(
            employee=employee, date=date,
            defaults={'check_in': check_in, 'check_out': check_out, 'note': note}
        )
        if not created:
            attendance.check_in = check_in
            attendance.check_out = check_out
            attendance.note = note
            attendance.save()

        messages.success(request, f'✅ Đã lưu chấm công cho {employee.name}')
        return redirect('attendance_list')

    today = dt_date.today()
    return render(request, 'cafe/attendance_edit.html', {
        'employee': employee,
        'today': today.isoformat(),
    })


def attendance_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')
    att = get_object_or_404(Attendance, id=id)
    att.delete()
    messages.success(request, '✅ Đã xóa bản ghi chấm công')
    return redirect('attendance_list')


# ==================== THỐNG KÊ DOANH THU ====================

def revenue_report(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    from datetime import date as dt_date, timedelta
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate

    today = dt_date.today()
    date_from_str = request.GET.get('date_from', (today - timedelta(days=29)).isoformat())
    date_to_str = request.GET.get('date_to', today.isoformat())

    from django.utils.dateparse import parse_date
    date_from = parse_date(date_from_str) or (today - timedelta(days=29))
    date_to = parse_date(date_to_str) or today

    # Doanh thu theo ngày (chỉ đơn hoàn thành)
    daily_qs = (
        Order.objects
        .filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(revenue=Sum('total_price'), orders=Count('id'))
        .order_by('day')
    )

    labels = []
    revenues = []
    order_counts = []
    for row in daily_qs:
        labels.append(row['day'].strftime('%d/%m'))
        revenues.append(row['revenue'] or 0)
        order_counts.append(row['orders'])

    # Top 5 sản phẩm bán chạy
    top_products = (
        OrderItem.objects
        .filter(order__status='completed', order__created_at__date__gte=date_from, order__created_at__date__lte=date_to)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price'))
        .order_by('-total_qty')[:5]
    )

    # Thống kê theo loại đơn
    order_type_stats = (
        Order.objects
        .filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to)
        .values('order_type')
        .annotate(count=Count('id'), revenue=Sum('total_price'))
    )
    order_type_map = {'dine_in': 'Tại quán', 'takeaway': 'Mang đi', 'delivery': 'Giao hàng'}
    type_labels = [order_type_map.get(r['order_type'], r['order_type']) for r in order_type_stats]
    type_counts = [r['count'] for r in order_type_stats]
    type_revenues = [r['revenue'] or 0 for r in order_type_stats]

    # Tổng quan
    total_revenue = sum(revenues)
    total_orders = sum(order_counts)
    avg_daily = round(total_revenue / max(len(labels), 1))

    return render(request, 'cafe/revenue_report.html', {
        'date_from': date_from_str,
        'date_to': date_to_str,
        'labels': labels,
        'revenues': revenues,
        'order_counts': order_counts,
        'top_products': top_products,
        'type_labels': type_labels,
        'type_counts': type_counts,
        'type_revenues': type_revenues,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_daily': avg_daily,
    })


# ==================== LỌC ĐƠN HÀNG (override order_list) ====================
# Lưu ý: hàm order_list gốc ở trên cần được cập nhật để hỗ trợ filter.
# Thêm hàm order_list_filtered với URL riêng để không phá vỡ gốc.
def order_list_filtered(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    from django.utils.dateparse import parse_date

    qs = Order.objects.all().prefetch_related('orderitem_set').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('order_type', '')
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    search = request.GET.get('search', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(order_type=type_filter)
    if date_from_str:
        df = parse_date(date_from_str)
        if df:
            qs = qs.filter(created_at__date__gte=df)
    if date_to_str:
        dt = parse_date(date_to_str)
        if dt:
            qs = qs.filter(created_at__date__lte=dt)
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(customer_name__icontains=search) | Q(customer_phone__icontains=search))

    status_choices = Order.STATUS_CHOICES
    type_choices = Order.ORDER_TYPE_CHOICES

    return render(request, 'cafe/order_list_filtered.html', {
        'orders': qs,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'search': search,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'total_count': qs.count(),
    })


# ================= TÍNH NĂNG MỚI: ĐẶT BÀN & ĐIỂM THƯỞNG & ĐÁNH GIÁ =================

# --- 1. LOYALTY ---
def api_check_loyalty(request):
    """API AJAX kiểm tra SĐT lấy thông tin Điểm và Hạng"""
    phone = request.GET.get('phone', '').strip()
    if not phone:
        return JsonResponse({'valid': False})
    
    from .models import CustomerProfile
    try:
        profile = CustomerProfile.objects.get(phone=phone)
        discount_percent = 0
        if profile.rank == 'Vàng':
            discount_percent = 10
        elif profile.rank == 'Bạc':
            discount_percent = 5
            
        return JsonResponse({
            'valid': True,
            'name': profile.name,
            'points': profile.points,
            'rank': profile.rank,
            'discount_percent': discount_percent
        })
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'valid': False})

# --- 2. RESERVATION ---
RESERVATION_SLOT_MINUTES = 120
RESERVATION_HOLD_MINUTES = 30


def _reservation_datetime_range(date_value, time_value):
    from datetime import datetime, timedelta

    start_dt = datetime.combine(date_value, time_value)
    end_dt = start_dt + timedelta(minutes=RESERVATION_SLOT_MINUTES)
    return start_dt, end_dt


def _sync_expired_reservations():
    from .models import Reservation

    now = timezone.localtime()
    expired_reservations = Reservation.objects.filter(
        status__in=['pending', 'confirmed'],
        hold_expires_at__isnull=False,
        hold_expires_at__lt=now,
    ).select_related('table')

    for reservation in expired_reservations:
        reservation.status = 'expired'
        reservation.save(update_fields=['status'])

        if reservation.table and reservation.table.status == 'reserved':
            reservation.table.status = 'available'
            reservation.table.save(update_fields=['status'])


def _find_conflicting_reservation(branch_id, date_value, time_value, table_id, exclude_id=None):
    from .models import Reservation

    if not table_id:
        return None

    req_start, req_end = _reservation_datetime_range(date_value, time_value)
    reservations = Reservation.objects.filter(
        branch_id=branch_id,
        table_id=table_id,
        date=date_value,
        status__in=['pending', 'confirmed', 'seated'],
    )

    if exclude_id:
        reservations = reservations.exclude(id=exclude_id)

    for reservation in reservations:
        existing_start, existing_end = _reservation_datetime_range(reservation.date, reservation.time)
        if existing_start < req_end and existing_end > req_start:
            return reservation
    return None


def reserve_table(request):
    """Trang cho KHÁCH HÀNG đặt bàn"""
    from datetime import date as dt_date
    from .models import Reservation, CafeBranch
    _sync_expired_reservations()
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', '').strip()
        branch_id = request.POST.get('branch_id')
        branch = get_object_or_404(CafeBranch, id=branch_id)
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        guests = int(request.POST.get('guests', 2))
        note = request.POST.get('note', '')

        table_id = request.POST.get('table_id')
        service_type = request.POST.get('service_type')
        
        table = None
        from datetime import datetime, timedelta
        from .models import Table
        from django.utils.dateparse import parse_date, parse_time

        reservation_date = parse_date(date_str)
        reservation_time = parse_time(time_str)

        if not reservation_date or not reservation_time:
            messages.error(request, '❌ Ngày hoặc giờ đặt bàn không hợp lệ')
            return redirect('reserve_table')

        reservation_dt = timezone.make_aware(datetime.combine(reservation_date, reservation_time))
        if reservation_dt <= timezone.localtime():
            messages.error(request, '❌ Vui lòng chọn thời gian đặt bàn ở tương lai')
            return redirect('reserve_table')

        if table_id:
            table = get_object_or_404(Table, id=table_id)
            if table.branch_id != branch.id:
                messages.error(request, '❌ Bàn đã chọn không thuộc chi nhánh này')
                return redirect('reserve_table')

            conflict = _find_conflicting_reservation(branch.id, reservation_date, reservation_time, table.id)
            if conflict:
                messages.error(
                    request,
                    f'❌ Bàn {table.number} đã có khách đặt gần khung giờ này. Vui lòng chọn bàn hoặc giờ khác.'
                )
                return redirect('reserve_table')

        hold_expires_at = reservation_dt + timedelta(minutes=RESERVATION_HOLD_MINUTES)

        reservation = Reservation.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email or None,
            branch=branch,
            table=table,
            date=reservation_date,
            time=reservation_time,
            guests=guests,
            note=note,
            is_preordered=(service_type == 'preorder'),
            hold_expires_at=hold_expires_at,
        )
        
        # Gửi email xác nhận đặt bàn
        from .services.email_service import send_reservation_confirmation_email
        send_reservation_confirmation_email(reservation)
        
        if service_type == 'preorder':
            request.session['reservation_id'] = reservation.id
            messages.success(request, '⏳ Đã xác nhận giữ bàn. Xin mời CHỌN MÓN để hoàn tất Đặt Cọc (30%).')
            return redirect('user_menu')
        else:
            messages.success(request, '🎉 Đặt bàn thành công! Mã Đặt bàn của bạn đã được ghi nhận.')
            return redirect('reservation_status')
        
    branches = CafeBranch.objects.filter(is_active=True)
    return render(request, 'cafe/reserve_table.html', {
        'branches': branches,
        'min_date': dt_date.today().isoformat()
    })

def admin_reservations(request):
    """Admin quản lý các yêu cầu đặt bàn"""
    if 'admin_id' not in request.session:
        return redirect('login')
    
    from .models import Reservation
    _sync_expired_reservations()
    queries = Reservation.objects.all().order_by('-date', '-time')
    return render(request, 'cafe/admin_reservations.html', {'reservations': queries})

def admin_reservation_status(request, id, status):
    """Admin duyệt / hủy / hoàn thành đặt bàn"""
    if 'admin_id' not in request.session:
        return redirect('login')
        
    from .models import Reservation
    _sync_expired_reservations()
    res = get_object_or_404(Reservation, id=id)
    allowed_transitions = {
        'pending': ['confirmed', 'cancelled', 'expired'],
        'confirmed': ['seated', 'cancelled', 'expired'],
        'seated': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': [],
        'expired': [],
    }

    if status in dict(Reservation.STATUS_CHOICES).keys():
        if status not in allowed_transitions.get(res.status, []):
            messages.error(request, '❌ Không thể chuyển trạng thái đặt bàn theo cách này')
            return redirect('admin_reservations')

        if status in ['confirmed', 'seated'] and res.table_id:
            conflict = _find_conflicting_reservation(
                res.branch_id,
                res.date,
                res.time,
                res.table_id,
                exclude_id=res.id,
            )
            if conflict:
                messages.error(
                    request,
                    f'❌ Bàn {res.table.number} đã bị trùng với một reservation khác trong cùng khung giờ.'
                )
                return redirect('admin_reservations')

        old_status = res.status
        res.status = status
        res.save(update_fields=['status'])
        
        # Đồng bộ trạng thái Bàn
        if res.table:
            if status == 'confirmed':
                res.table.status = 'reserved'
            elif status == 'seated':
                res.table.status = 'occupied'
            elif status in ['completed', 'cancelled', 'expired']:
                res.table.status = 'available'
            res.table.save(update_fields=['status'])
            
        # Gửi email cập nhật trạng thái đặt bàn
        if old_status != status:
            from .services.email_service import send_reservation_status_update_email
            send_reservation_status_update_email(res, old_status=old_status)
            
        messages.success(request, f'✅ Cập nhật trạng thái đặt bàn thành {status}')
    return redirect('admin_reservations')

# --- 3. REVIEWS ---
def submit_review(request, order_id, product_id):
    """Khách hàng gửi review cho từng sản phẩm trong đơn hàng đã hoàn tất"""
    order = get_object_or_404(Order, id=order_id)
    product = get_object_or_404(Product, id=product_id)

    if order.status != 'completed':
        messages.error(request, '❌ Chỉ đơn hàng hoàn tất mới được đánh giá')
        return redirect('user_order_detail')

    from .models import Review
    
    # Kiểm tra xem đã đánh giá món này trong đơn này chưa
    if Review.objects.filter(order=order, product=product).exists():
        messages.warning(request, f'⚠ Bạn đã đánh giá món {product.name} rồi.')
        return redirect('user_order_detail')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')

        Review.objects.create(
            order=order,
            product=product,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            rating=rating,
            comment=comment
        )
        messages.success(request, f'🌟 Cảm ơn bạn đã gửi đánh giá cho {product.name}!')
        return redirect('user_order_detail')

    return render(request, 'cafe/submit_review.html', {'order': order, 'product': product})

def admin_reviews(request):
    """Admin xem tất cả đánh giá"""
    if 'admin_id' not in request.session:
        return redirect('login')
        
    from .models import Review
    reviews = Review.objects.all().select_related('order', 'order__branch').order_by('-created_at')
    return render(request, 'cafe/admin_reviews.html', {'reviews': reviews})

# --- 4. GIS NÂNG CAO (HEATMAP ĐƠN HÀNG) ---
def api_orders_heatmap(request):
    """API trả về danh sách tọa độ các đơn hàng đã giao thành công để vẽ Heatmap"""
    orders = Order.objects.filter(
        status='completed', 
        customer_lat__isnull=False, 
        customer_lng__isnull=False
    ).values('customer_lat', 'customer_lng', 'total_price')
    
    data = []
    for o in orders:
        try:
            lat = float(o['customer_lat'])
            lng = float(o['customer_lng'])
            # Intensity dựa trên số tiền đơn hàng (VD: đơn lớn thì nóng hơn)
            intensity = 1.0 + (float(o['total_price']) / 100000.0) 
            data.append([lat, lng, intensity])
        except (ValueError, TypeError):
            continue
            
    return JsonResponse(data, safe=False)

# --- 5. TÌM BÀN TRỐNG ---
def api_available_tables(request):
    branch_id = request.GET.get('branch_id')
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    if not all([branch_id, date_str, time_str]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    from datetime import datetime
    from .models import Table, Reservation
    _sync_expired_reservations()
    
    try:
        req_time = datetime.strptime(time_str, '%H:%M').time()
        req_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        req_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    except ValueError:
        return JsonResponse({'error': 'Invalid format'}, status=400)
    
    all_tables = Table.objects.filter(branch_id=branch_id)
    
    conflicting_reservations = Reservation.objects.filter(
        branch_id=branch_id,
        date=req_date,
        status__in=['pending', 'confirmed', 'seated']
    )
    
    busy_table_ids = []
    for res in conflicting_reservations:
        if res.table_id:
            existing_start, existing_end = _reservation_datetime_range(res.date, res.time)
            req_start, req_end = _reservation_datetime_range(req_date, req_time)
            if existing_start < req_end and existing_end > req_start:
                busy_table_ids.append(res.table_id)
                
    available_tables = all_tables.exclude(id__in=busy_table_ids).values('id', 'number', 'capacity')
    return JsonResponse({'tables': list(available_tables)})

def reservation_status(request):
    """Trang tra cứu Đặt bàn cho Khách bằng SĐT"""
    from .models import Reservation
    _sync_expired_reservations()
    phone = request.GET.get('phone', '').strip()
    reservations = []
    if phone:
        reservations = Reservation.objects.filter(customer_phone=phone).order_by('-date', '-time')
    return render(request, 'cafe/reservation_status.html', {'reservations': reservations, 'phone': phone})

# ==================== DASHBOARD THỐNG KÊ TỔNG QUAN ====================
@role_required('admin', 'cashier')
def admin_dashboard(request):

    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # Tổng quan
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    month_revenue = Order.objects.filter(status='completed', created_at__date__gte=this_month_start).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_branches = CafeBranch.objects.count()
    total_employees = Employee.objects.count()
    total_products = Product.objects.count()
    
    # Top 5 sản phẩm bán chạy
    top_products = OrderItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]
    
    # Doanh thu 6 tháng gần nhất
    monthly_revenue = Order.objects.filter(status='completed').annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_price')
    ).order_by('-month')[:6]
    monthly_revenue = list(reversed(monthly_revenue))
    
    # Chi nhánh hoạt động tốt nhất
    branch_stats = []
    for branch in CafeBranch.objects.filter(is_active=True)[:10]:
        rev = Order.objects.filter(branch=branch, status='completed', created_at__date__gte=this_month_start).aggregate(Sum('total_price'))['total_price__sum'] or 0
        orders_count = Order.objects.filter(branch=branch, created_at__date=today).count()
        branch_stats.append({'name': branch.name, 'revenue': rev, 'orders': orders_count})
    branch_stats.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Nguyên liệu sắp hết / đã hết
    low_materials = RawMaterial.objects.filter(
        quantity__lte=models.F('min_quantity')
    ).order_by('quantity')
    
    return render(request, 'cafe/admin_dashboard.html', {
        'total_orders': total_orders,
        'today_orders': today_orders,
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'total_branches': total_branches,
        'total_employees': total_employees,
        'total_products': total_products,
        'top_products': top_products,
        'monthly_revenue': monthly_revenue,
        'branch_stats': branch_stats,
        'low_materials': low_materials,
    })

# ==================== QUẢN LÝ NHÀ CUNG CẤP ====================
@role_required('admin')
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('-created_at')
    return render(request, 'cafe/supplier_list.html', {'suppliers': suppliers})

@role_required('admin')
def supplier_add(request):
    if request.method == 'POST':
        s = Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST.get('phone'),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            notes=request.POST.get('notes', ''),
        )
        # Thêm đơn nhập hàng nếu có
        ingredient_id = request.POST.get('ingredient_id')
        if ingredient_id:
            mat = RawMaterial.objects.get(id=ingredient_id)
            qty = float(request.POST.get('qty', 0))
            unit_price = int(request.POST.get('unit_price', 0))
            SupplierOrder.objects.create(
                supplier=s, ingredient=mat, quantity=qty,
                unit_price=unit_price, total_price=int(qty * unit_price)
            )
            mat.quantity += qty
            mat.save()
        return redirect('supplier_list')
    materials = RawMaterial.objects.all()
    return render(request, 'cafe/supplier_add.html', {'materials': materials})

# ==================== QUẢN LÝ CA LÀM VIỆC ====================
@role_required('admin')
def shift_list(request):
    branch_id = request.GET.get('branch')
    date_filter = request.GET.get('date')
    shifts = WorkShift.objects.all().order_by('-date')
    if branch_id:
        shifts = shifts.filter(branch_id=branch_id)
    if date_filter:
        shifts = shifts.filter(date=date_filter)
    branches = CafeBranch.objects.filter(is_active=True)
    return render(request, 'cafe/shift_list.html', {'shifts': shifts, 'branches': branches})

@role_required('admin')
def shift_add(request):
    if request.method == 'POST':
        shift, created = WorkShift.objects.get_or_create(
            branch_id=request.POST.get('branch_id'),
            shift_type=request.POST.get('shift_type'),
            date=request.POST.get('date'),
            defaults={'notes': request.POST.get('notes', '')}
        )
        emp_ids = request.POST.getlist('employees')
        for eid in emp_ids:
            ShiftAssignment.objects.get_or_create(shift=shift, employee_id=eid)
        return redirect('shift_list')
    branches = CafeBranch.objects.filter(is_active=True)
    employees = Employee.objects.all()
    return render(request, 'cafe/shift_add.html', {'branches': branches, 'employees': employees})

# ==================== LỊCH SỬ MUA KHÁCH HÀNG ====================
def customer_history(request):
    phone = request.GET.get('phone', '').strip()
    orders = []
    loyalty = None
    if phone:
        orders = Order.objects.prefetch_related('orderitem_set__product').filter(customer_phone=phone).order_by('-created_at')
        loyalty = None
        
        from .models import Review
        user_reviews = Review.objects.filter(customer_phone=phone)
        reviewed_keys = {(r.order_id, r.product_id): r for r in user_reviews}  # type: ignore
        
        for order in orders:
            # Gán trực tiếp vào list (không dùng queryset lazy) để attribute được giữ lại trong template
            items_list = list(order.orderitem_set.all())
            setattr(order, 'items_list', items_list)
            for item in items_list:
                key = (order.id, item.product_id)
                if key in reviewed_keys:
                    setattr(item, 'has_reviewed', True)
                    setattr(item, 'rating_given', getattr(reviewed_keys[key], 'rating', 5))  # type: ignore
                else:
                    setattr(item, 'has_reviewed', False)

    return render(request, 'cafe/customer_history.html', {
        'orders': orders, 'loyalty': loyalty, 'phone': phone
    })


# ==================== API CHỌN CHI NHÁNH TỐI ƯU ====================

def api_optimal_branch(request):
    """API trả kết quả chọn chi nhánh tối ưu cho giao hàng."""
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Sai tham số lat/lng"}, status=400)

    result = find_optimal_branch(lat, lng)

    if not result:
        return JsonResponse({
            "found": False,
            "message": "Không có chi nhánh nào giao được tới vị trí này"
        })

    branch = result['branch']
    distance = result['distance']

    # Tính phí
    if distance <= 1000:
        fee = 10000
    elif distance <= 3000:
        fee = 15000
    else:
        fee = 20000

    # Danh sách ứng viên
    candidates_list = []
    for c in result.get('candidates', []):
        candidates_list.append({
            'name': c['name'],
            'distance': c['distance'],
            'today_orders': c.get('today_orders', 0),
        })

    return JsonResponse({
        "found": True,
        "branch": {
            "id": branch.id,
            "name": branch.name,
            "address": branch.address,
            "lat": branch.location.y,
            "lng": branch.location.x,
        },
        "distance": distance,
        "fee": fee,
        "reason": result.get('reason', ''),
        "candidates": candidates_list,
    })


# ==================== THỐNG KÊ GIS THEO CHI NHÁNH ====================

@role_required('admin', 'cashier')
def branch_analytics(request):
    """Trang phân tích GIS theo chi nhánh"""
    return render(request, 'cafe/branch_analytics.html')


def api_branch_analytics(request):
    """API thống kê chi nhánh + tọa độ cho bản đồ phân tích"""
    from django.db.models import Sum, Count, Avg

    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    branches = CafeBranch.objects.filter(is_active=True)
    result = []
    max_revenue = 0

    for b in branches:
        # Doanh thu tổng (completed)
        total_revenue = Order.objects.filter(
            branch=b, status='completed'
        ).aggregate(s=Sum('total_price'))['s'] or 0

        # Doanh thu tháng này
        month_revenue = Order.objects.filter(
            branch=b, status='completed',
            created_at__date__gte=this_month_start
        ).aggregate(s=Sum('total_price'))['s'] or 0

        # Tổng đơn
        total_orders = Order.objects.filter(branch=b).count()

        # Đơn hôm nay
        today_orders = Order.objects.filter(
            branch=b, created_at__date=today
        ).count()

        # Đơn delivery
        delivery_orders = Order.objects.filter(
            branch=b, order_type='delivery'
        ).count()

        # Đánh giá trung bình
        from .models import Review
        avg_rating = Review.objects.filter(
            order__branch=b
        ).aggregate(avg=Avg('rating'))['avg']

        if total_revenue > max_revenue:
            max_revenue = total_revenue

        result.append({
            'id': b.id,
            'name': b.name,
            'address': b.address,
            'phone': b.phone,
            'lat': b.location.y,
            'lng': b.location.x,
            'delivery_radius': b.delivery_radius,
            'total_revenue': total_revenue,
            'month_revenue': month_revenue,
            'total_orders': total_orders,
            'today_orders': today_orders,
            'delivery_orders': delivery_orders,
            'avg_rating': round(avg_rating, 1) if avg_rating else None,
        })

    return JsonResponse({
        'branches': result,
        'max_revenue': max_revenue,
        'report_date': today.strftime('%d/%m/%Y'),
    })


# ==================== ADMIN QUẢN LÝ GIAO HÀNG ====================

def _get_current_app_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()


def _delivery_json_or_redirect(request, success, message, status=200):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': success, 'message': message}, status=status)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('shipper_deliveries')


def _shipper_action_error(request, message, status=400):
    return _delivery_json_or_redirect(request, False, message, status=status)


def _shipper_action_success(request, message):
    return _delivery_json_or_redirect(request, True, message)


def _can_admin_assign_shipper(order):
    """Kiểm tra admin có thể gán shipper cho đơn không."""
    if order.order_type != 'delivery':
        return False
    if order.status in ['completed', 'cancelled']:
        return False
    # Cho phép gán ở cả trạng thái ready_for_delivery (món đã pha xong, chờ lấy)
    if order.status not in ['confirmed', 'preparing', 'ready_for_delivery', 'delivering']:
        return False
    if order.delivery_status in ['not_required', 'delivered', 'shipping']:
        return False
    return True


def _can_shipper_start_delivery(order):
    """Shipper có thể bắt đầu giao đơn không.
    
    Luồng mới:
    - Admin đổi status: pending → confirmed → preparing → ready_for_delivery
    - Admin gán shipper: delivery_status = 'assigned' (status vẫn là ready_for_delivery)
    - Shipper nhận đơn: delivery_status = 'accepted' (order.status vẫn là ready_for_delivery)
    - Shipper bắt đầu giao: delivery_status = 'shipping', order.status = 'delivering'
    
    Điều kiện để bắt đầu giao:
    - delivery_status = 'accepted' (đã nhận đơn)
    - order.status phải là 'ready_for_delivery' (món đã pha xong)
    - KHÔNG cần kiểm tra order.status = 'delivering' vì ở bước này order.status vẫn là ready_for_delivery
    """
    if order.order_type != 'delivery':
        return False
    if order.status not in ['ready_for_delivery', 'delivering']:
        return False
    if order.delivery_status != 'accepted':
        return False
    return True


def _can_shipper_complete_delivery(order):
    """Shipper có thể hoàn tất giao đơn không.
    
    Điều kiện:
    - delivery_status = 'shipping' (đang giao)
    - order.status phải là 'delivering' hoặc 'ready_for_delivery'
      (trường hợp ready_for_delivery xảy ra khi admin/shipper bỏ qua bước accepted)
    """
    if order.order_type != 'delivery':
        return False
    if order.status not in ['ready_for_delivery', 'delivering']:
        return False
    if order.delivery_status not in ['shipping', 'accepted']:
        return False
    return True


def _get_shipper_orders_queryset(request):
    current_user = _get_current_app_user(request)
    user_role = request.session.get('user_role', '')

    orders = (
        Order.objects
        .filter(order_type='delivery')
        .select_related('branch', 'assigned_shipper')
        .order_by('-created_at')
    )

    if user_role == 'shipper' and current_user:
        return orders.filter(
            assigned_shipper=current_user,
            delivery_status__in=['assigned', 'accepted', 'shipping']
        )

    return orders.filter(delivery_status__in=['waiting', 'assigned', 'accepted', 'shipping', 'failed'])


@role_required('admin')
@require_POST
def admin_assign_shipper(request, order_id):
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not _can_admin_assign_shipper(order):
        messages.error(request, '❌ Đơn này không thể gán shipper ở trạng thái hiện tại')
        return redirect('admin_deliveries')

    shipper_id = request.POST.get('shipper_id', '').strip()
    shipper = User.objects.filter(id=shipper_id, role='shipper').first()

    if not shipper:
        messages.error(request, '❌ Vui lòng chọn đúng tài khoản shipper')
        return redirect('admin_deliveries')

    order.assigned_shipper = shipper
    order.assigned_at = timezone.now()
    order.accepted_at = None
    order.started_delivery_at = None
    order.delivered_at = None
    order.failed_at = None
    order.failure_reason = ''
    order.delivery_status = 'assigned'
    order.delivery_attempt_count += 1

    if order.status == 'delivering':
        order.status = 'confirmed'

    order.save()
    messages.success(request, f'✅ Đã gán Đơn #{order.id} cho shipper {shipper.username}')
    return redirect('admin_deliveries')

@role_required('admin')
def admin_deliveries(request):
    """Trang admin quản lý tổng quan các đơn giao hàng"""
    status_filter = request.GET.get('status', 'all')
    
    orders = (
        Order.objects
        .filter(order_type='delivery')
        .select_related('branch', 'assigned_shipper')
        .order_by('-created_at')
    )
    
    if status_filter == 'waiting':
        orders = orders.filter(delivery_status='waiting')
    elif status_filter == 'assigned':
        orders = orders.filter(delivery_status='assigned')
    elif status_filter == 'accepted':
        orders = orders.filter(delivery_status='accepted')
    elif status_filter == 'shipping':
        orders = orders.filter(delivery_status='shipping')
    elif status_filter == 'delivered':
        orders = orders.filter(delivery_status='delivered')
    elif status_filter == 'failed':
        orders = orders.filter(delivery_status='failed')

    return render(request, 'cafe/admin_deliveries.html', {
        'orders': orders,
        'current_status': status_filter,
        'shippers': User.objects.filter(role='shipper').order_by('username'),
    })


# ==================== SHIPPER GIAO HÀNG ====================

@role_required('shipper', 'admin')
def shipper_deliveries(request):
    """Trang shipper xem đơn giao hàng trên bản đồ"""
    return render(request, 'cafe/shipper_deliveries.html')


def api_shipper_deliveries(request):
    """API trả JSON danh sách đơn giao hàng cho shipper map"""
    current_user = _get_current_app_user(request)
    orders = _get_shipper_orders_queryset(request)

    result = []
    for o in orders:
        # Chỉ lấy đơn có tọa độ khách
        if not o.customer_lat or not o.customer_lng:
            continue

        branch_data = None
        if o.branch and o.branch.location:
            branch_data = {
                'name': o.branch.name,
                'address': o.branch.address,
                'lat': o.branch.location.y,
                'lng': o.branch.location.x,
            }

        result.append({
            'id': o.id,
            'customer_name': o.customer_name,
            'customer_phone': o.customer_phone,
            'customer_address': o.customer_address,
            'customer_lat': o.customer_lat,
            'customer_lng': o.customer_lng,
            'status': o.get_status_display(),
            'status_code': o.status,
            'delivery_status': o.get_delivery_status_display(),
            'delivery_status_code': o.delivery_status,
            'delivery_fee': o.delivery_fee,
            'delivery_distance': round(o.delivery_distance, 0),
            'total_price': o.total_price,
            'created_at': o.created_at.strftime('%H:%M %d/%m'),
            'note': o.note,
            'assigned_shipper_id': o.assigned_shipper_id,
            'assigned_shipper_name': o.assigned_shipper.username if o.assigned_shipper else '',
            'assigned_at': o.assigned_at.strftime('%H:%M %d/%m') if o.assigned_at else '',
            'accepted_at': o.accepted_at.strftime('%H:%M %d/%m') if o.accepted_at else '',
            'started_delivery_at': o.started_delivery_at.strftime('%H:%M %d/%m') if o.started_delivery_at else '',
            'delivered_at': o.delivered_at.strftime('%H:%M %d/%m') if o.delivered_at else '',
            'failed_at': o.failed_at.strftime('%H:%M %d/%m') if o.failed_at else '',
            'failure_reason': o.failure_reason,
            'delivery_attempt_count': o.delivery_attempt_count,
            'is_mine': bool(current_user and o.assigned_shipper_id == current_user.id),
            'branch': branch_data,
        })

    return JsonResponse(result, safe=False)


@role_required('shipper')
@require_POST
def shipper_accept_delivery(request, order_id):
    current_user = _get_current_app_user(request)
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not current_user or order.assigned_shipper_id != current_user.id:
        return _shipper_action_error(request, '❌ Bạn không được thao tác trên đơn này', status=403)
    if order.delivery_status != 'assigned':
        return _shipper_action_error(request, '❌ Chỉ đơn đã được gán mới có thể nhận')
    # ✅ Luồng mới: cho phép nhận ở cả ready_for_delivery (món đã pha xong)
    if order.status not in ['confirmed', 'preparing', 'ready_for_delivery']:
        return _shipper_action_error(request, '❌ Đơn chưa sẵn sàng để shipper nhận')

    order.delivery_status = 'accepted'
    order.accepted_at = timezone.now()
    order.failed_at = None
    order.failure_reason = ''
    order.save()
    return _shipper_action_success(request, f'✅ Bạn đã nhận Đơn #{order.id}')


@role_required('shipper')
@require_POST
def shipper_reject_delivery(request, order_id):
    current_user = _get_current_app_user(request)
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not current_user or order.assigned_shipper_id != current_user.id:
        return _shipper_action_error(request, '❌ Bạn không được thao tác trên đơn này', status=403)
    if order.delivery_status not in ['assigned', 'accepted']:
        return _shipper_action_error(request, '❌ Chỉ đơn chờ nhận hoặc đã nhận mới có thể từ chối')

    reason = request.POST.get('reason', '').strip() or 'Shipper từ chối nhận đơn'
    order.delivery_status = 'waiting'
    order.failed_at = timezone.now()
    order.failure_reason = reason
    order.accepted_at = None
    order.started_delivery_at = None
    if order.status == 'delivering':
        order.status = 'confirmed'
    order.save()
    return _shipper_action_success(request, f'✅ Đã trả Đơn #{order.id} về trạng thái chờ gán')


@role_required('shipper')
@require_POST
def shipper_start_delivery(request, order_id):
    """Bắt đầu giao đơn - shipper lấy hàng từ quán và bắt đầu delivery.
    
    Luồng mới:
    - Điều kiện: delivery_status='accepted' AND status='ready_for_delivery' (món đã pha xong)
    - Kết quả: delivery_status='shipping', status='delivering'
    """
    current_user = _get_current_app_user(request)
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not current_user or order.assigned_shipper_id != current_user.id:
        return _shipper_action_error(request, '❌ Bạn không được thao tác trên đơn này', status=403)
    if not _can_shipper_start_delivery(order):
        return _shipper_action_error(
            request, 
            '❌ Bạn phải NHẬN ĐƠN trước khi bắt đầu giao. '
            'Đơn cần có trạng thái "Chờ lấy hàng" và bạn đã nhận đơn.'
        )

    if not order.accepted_at:
        order.accepted_at = timezone.now()
    order.delivery_status = 'shipping'
    order.started_delivery_at = timezone.now()
    order.status = 'delivering'
    order.save()
    return _shipper_action_success(request, f'✅ Đã bắt đầu giao Đơn #{order.id}')


@role_required('shipper')
@require_POST
def shipper_complete_delivery(request, order_id):
    current_user = _get_current_app_user(request)
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not current_user or order.assigned_shipper_id != current_user.id:
        return _shipper_action_error(request, '❌ Bạn không được thao tác trên đơn này', status=403)
    if order.delivery_status != 'shipping':
        return _shipper_action_error(request, '❌ Chỉ đơn đang giao mới có thể hoàn tất')
    if order.status != 'delivering':
        return _shipper_action_error(request, '❌ Trạng thái đơn chính không khớp với luồng giao hàng')

    old_status = order.status
    order.delivery_status = 'delivered'
    order.delivered_at = timezone.now()
    order.status = 'completed'
    order.failure_reason = ''
    order.failed_at = None
    order.save()

    if order.customer_phone:
        profile, _ = CustomerProfile.objects.get_or_create(
            phone=order.customer_phone,
            defaults={'name': order.customer_name}
        )
        profile.total_spent += order.total_price
        profile.points += int(order.total_price * 0.05)
        profile.update_rank()

    if old_status != 'completed':
        from .services.email_service import send_order_status_update_email
        send_order_status_update_email(order, old_status=old_status)

    return _shipper_action_success(request, f'✅ Đã xác nhận giao thành công Đơn #{order.id}')


@role_required('shipper')
@require_POST
def shipper_fail_delivery(request, order_id):
    current_user = _get_current_app_user(request)
    order = get_object_or_404(Order, id=order_id, order_type='delivery')

    if not current_user or order.assigned_shipper_id != current_user.id:
        return _shipper_action_error(request, '❌ Bạn không được thao tác trên đơn này', status=403)
    if order.delivery_status not in ['accepted', 'shipping']:
        return _shipper_action_error(request, '❌ Chỉ đơn đã nhận hoặc đang giao mới có thể báo thất bại')
    if order.delivery_status == 'accepted' and order.status not in ['confirmed', 'preparing']:
        return _shipper_action_error(request, '❌ Trạng thái đơn hiện tại không cho phép báo thất bại ở bước này')
    if order.delivery_status == 'shipping' and order.status != 'delivering':
        return _shipper_action_error(request, '❌ Trạng thái đơn chính không khớp với luồng giao hàng')

    reason = request.POST.get('reason', '').strip()
    if not reason:
        return _shipper_action_error(request, '❌ Vui lòng nhập lý do giao thất bại')

    order.delivery_status = 'failed'
    order.failed_at = timezone.now()
    order.failure_reason = reason
    if order.status == 'delivering':
        order.status = 'confirmed'
    order.save()
    return _shipper_action_success(request, f'✅ Đã ghi nhận giao thất bại cho Đơn #{order.id}')


# ==================== IMPORT / EXPORT EXCEL ====================

def import_materials_excel(request):
    """Import nguyên vật liệu từ file Excel (.xlsx)"""
    if 'admin_id' not in request.session:
        return redirect('login')

    branches = CafeBranch.objects.filter(is_active=True).order_by('name')
    selected_branch = None
    branch_id = request.GET.get('branch_id') or request.POST.get('branch_id')
    if branch_id:
        selected_branch = CafeBranch.objects.filter(id=branch_id, is_active=True).first()

    context = {
        'import_done': False,
        'branches': branches,
        'selected_branch': selected_branch,
    }

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, '❌ Vui lòng chọn file Excel.')
            return render(request, 'cafe/import_materials.html', context)

        if not excel_file.name.endswith('.xlsx'):
            messages.error(request, '❌ Chỉ hỗ trợ file .xlsx (Excel 2007+).')
            return render(request, 'cafe/import_materials.html', context)

        from cafe.services.excel_service import import_materials_from_excel
        result = import_materials_from_excel(excel_file, branch=selected_branch)

        context['import_done'] = True
        context['created_count'] = result['created_count']
        context['updated_count'] = result['updated_count']
        context['error_messages'] = result['error_messages']
        context['error_count'] = len(result['error_messages'])

        if result['success']:
            total = result['created_count'] + result['updated_count']
            messages.success(request, f'✅ Import thành công! Tạo mới: {result["created_count"]}, Cập nhật: {result["updated_count"]}')
        else:
            messages.error(request, '❌ Import thất bại. Kiểm tra chi tiết lỗi bên dưới.')

    return render(request, 'cafe/import_materials.html', context)


def download_material_template(request):
    """Tải file Excel mẫu cho import nguyên vật liệu."""
    if 'admin_id' not in request.session:
        return redirect('login')

    from cafe.services.excel_service import generate_material_template
    return generate_material_template()


def export_orders_excel(request):
    """Export danh sách đơn hàng ra file Excel (.xlsx).
    Hỗ trợ filter theo query params giống order_list_filtered."""
    if 'admin_id' not in request.session:
        return redirect('login')

    from django.utils.dateparse import parse_date

    qs = Order.objects.all().order_by('-created_at')

    # Áp dụng filter nếu có query params
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('order_type', '')
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    search = request.GET.get('search', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(order_type=type_filter)
    if date_from_str:
        df = parse_date(date_from_str)
        if df:
            qs = qs.filter(created_at__date__gte=df)
    if date_to_str:
        dt = parse_date(date_to_str)
        if dt:
            qs = qs.filter(created_at__date__lte=dt)
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(customer_name__icontains=search) | Q(customer_phone__icontains=search))

    from cafe.services.excel_service import export_orders_excel as _export
    return _export(qs)


def export_order_pdf(request, id):
    """Export hóa đơn đơn hàng dưới dạng PDF."""
    if 'admin_id' not in request.session:
        return redirect('login')

    order = get_object_or_404(Order, id=id)
    items = OrderItem.objects.filter(order=order).select_related('product')

    from cafe.services.pdf_service import export_order_pdf as _pdf
    return _pdf(order, items)


def _get_revenue_data(request):
    """Helper: tính dữ liệu báo cáo doanh thu (dùng chung cho Excel/PDF export)."""
    from datetime import date as dt_date, timedelta
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate
    from django.utils.dateparse import parse_date

    today = dt_date.today()
    date_from_str = request.GET.get('date_from', (today - timedelta(days=29)).isoformat())
    date_to_str = request.GET.get('date_to', today.isoformat())

    date_from = parse_date(date_from_str) or (today - timedelta(days=29))
    date_to = parse_date(date_to_str) or today

    daily_qs = (
        Order.objects
        .filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(revenue=Sum('total_price'), orders=Count('id'))
        .order_by('day')
    )

    labels = []
    revenues = []
    order_counts = []
    for row in daily_qs:
        labels.append(row['day'].strftime('%d/%m'))
        revenues.append(row['revenue'] or 0)
        order_counts.append(row['orders'])

    top_products = list(
        OrderItem.objects
        .filter(order__status='completed', order__created_at__date__gte=date_from, order__created_at__date__lte=date_to)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price'))
        .order_by('-total_qty')[:5]
    )

    order_type_stats = (
        Order.objects
        .filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to)
        .values('order_type')
        .annotate(count=Count('id'), revenue=Sum('total_price'))
    )
    order_type_map = {'dine_in': 'Tai quan', 'takeaway': 'Mang di', 'delivery': 'Giao hang'}
    type_labels = [order_type_map.get(r['order_type'], r['order_type']) for r in order_type_stats]
    type_counts = [r['count'] for r in order_type_stats]
    type_revenues = [r['revenue'] or 0 for r in order_type_stats]

    total_revenue = sum(revenues)
    total_orders = sum(order_counts)
    avg_daily = round(total_revenue / max(len(labels), 1))

    return {
        'date_from': date_from_str,
        'date_to': date_to_str,
        'labels': labels,
        'revenues': revenues,
        'order_counts': order_counts,
        'top_products': top_products,
        'type_labels': type_labels,
        'type_counts': type_counts,
        'type_revenues': type_revenues,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_daily': avg_daily,
    }


def export_revenue_excel_view(request):
    """Export báo cáo doanh thu ra file Excel."""
    if 'admin_id' not in request.session:
        return redirect('login')

    data = _get_revenue_data(request)
    from cafe.services.excel_service import export_revenue_excel
    return export_revenue_excel(data)


def export_revenue_pdf_view(request):
    """Export báo cáo doanh thu ra file PDF."""
    if 'admin_id' not in request.session:
        return redirect('login')

    data = _get_revenue_data(request)
    from cafe.services.pdf_service import export_revenue_pdf
    return export_revenue_pdf(data)


# ==================== ADMIN QUẢN LÝ SHIPPER ====================

@role_required('admin')
def admin_shipper_list(request):
    """Danh sách tài khoản shipper + profile của họ."""
    branch_id = request.GET.get('branch_id', '').strip()
    availability_filter = request.GET.get('availability', '')

    shippers = (
        User.objects
        .filter(role='shipper')
        .select_related('shipper_profile__assigned_branch')
        .order_by('username')
    )

    if branch_id:
        shippers = shippers.filter(shipper_profile__assigned_branch_id=branch_id)

    if availability_filter == 'available':
        shippers = shippers.filter(shipper_profile__is_available=True)
    elif availability_filter == 'busy':
        shippers = shippers.filter(shipper_profile__is_available=False)

    branches = CafeBranch.objects.filter(is_active=True).order_by('name')

    # Gán thêm stats cho từng shipper
    for s in shippers:
        try:
            profile = s.shipper_profile
            s.active_orders = profile.get_active_orders_count()
            s.can_accept = profile.can_accept_more_orders()
        except Exception:
            s.active_orders = 0
            s.can_accept = True

    return render(request, 'cafe/admin_shipper_list.html', {
        'shippers': shippers,
        'branches': branches,
        'selected_branch_id': branch_id,
        'availability_filter': availability_filter,
    })


@role_required('admin')
def admin_shipper_add(request):
    """Tạo tài khoản shipper mới + profile."""
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        phone = request.POST.get('phone', '').strip()
        branch_id = request.POST.get('branch_id')
        is_available = request.POST.get('is_available') == 'on'
        max_active_orders = int(request.POST.get('max_active_orders', 5))

        if not username or not password:
            messages.error(request, '❌ Vui lòng nhập tên đăng nhập và mật khẩu')
            return redirect('admin_shipper_add')

        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ Tên đăng nhập đã tồn tại')
            return redirect('admin_shipper_add')

        branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

        with transaction.atomic():
            user = User.objects.create(
                username=username,
                password=password,  # TODO: Nên hash password trong production
                role='shipper',
                is_admin=False,
            )

            from .models import ShipperProfile
            ShipperProfile.objects.create(
                user=user,
                phone=phone,
                assigned_branch=branch,
                is_available=is_available,
                max_active_orders=max_active_orders,
            )

        messages.success(request, f'✅ Đã tạo tài khoản shipper: {username}')
        return redirect('admin_shipper_list')

    return render(request, 'cafe/admin_shipper_form.html', {
        'shipper': None,
        'branches': branches,
    })


@role_required('admin')
def admin_shipper_edit(request, id):
    """Sửa thông tin shipper (profile)."""
    user = get_object_or_404(User, id=id, role='shipper')
    branches = CafeBranch.objects.filter(is_active=True).order_by('name')

    try:
        profile = user.shipper_profile
    except Exception:
        from .models import ShipperProfile
        profile = ShipperProfile.objects.create(
            user=user,
            phone='',
            assigned_branch=None,
            is_available=True,
            max_active_orders=5,
        )

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        branch_id = request.POST.get('branch_id')
        is_available = request.POST.get('is_available') == 'on'
        max_active_orders = int(request.POST.get('max_active_orders', 5))

        branch = CafeBranch.objects.filter(id=branch_id).first() if branch_id else None

        profile.phone = phone
        profile.assigned_branch = branch
        profile.is_available = is_available
        profile.max_active_orders = max_active_orders
        profile.save()

        messages.success(request, f'✅ Đã cập nhật thông tin shipper: {user.username}')
        return redirect('admin_shipper_list')

    return render(request, 'cafe/admin_shipper_form.html', {
        'shipper': user,
        'profile': profile,
        'branches': branches,
    })


@role_required('admin')
def admin_shipper_delete(request, id):
    """Xóa tài khoản shipper."""
    user = get_object_or_404(User, id=id, role='shipper')
    username = user.username

    # Kiểm tra còn đơn đang giao không
    active_orders = Order.objects.filter(
        assigned_shipper=user,
        delivery_status__in=['assigned', 'accepted', 'shipping']
    ).count()

    if active_orders > 0:
        messages.error(
            request,
            f'❌ Shipper {username} đang có {active_orders} đơn đang giao. Không thể xóa.'
        )
        return redirect('admin_shipper_list')

    user.delete()
    messages.success(request, f'✅ Đã xóa tài khoản shipper: {username}')
    return redirect('admin_shipper_list')


@role_required('admin')
def admin_shipper_toggle_availability(request, id):
    """Toggle trạng thái khả dụng của shipper (bật/tắt nhận đơn)."""
    user = get_object_or_404(User, id=id, role='shipper')

    try:
        profile = user.shipper_profile
    except Exception:
        messages.error(request, '❌ Shipper chưa có profile')
        return redirect('admin_shipper_list')

    profile.is_available = not profile.is_available
    profile.save()

    status_text = 'Đang nhận đơn' if profile.is_available else 'Tạm ngưng'
    messages.success(request, f'✅ Shipper {user.username}: {status_text}')
    return redirect('admin_shipper_list')


def api_shippers_by_branch(request):
    """API trả danh sách shipper theo chi nhánh (dùng cho dropdown gán shipper).
    
    Query params:
    - branch_id: ID chi nhánh
    - only_available: 1 để chỉ lấy shipper đang rảnh
    """
    branch_id = request.GET.get('branch_id', '').strip()
    only_available = request.GET.get('only_available', '0') == '1'

    if not branch_id:
        return JsonResponse({'error': 'Thiếu branch_id'}, status=400)

    try:
        branch_id_int = int(branch_id)
    except ValueError:
        return JsonResponse({'error': 'branch_id không hợp lệ'}, status=400)

    shippers = (
        User.objects
        .filter(role='shipper', shipper_profile__assigned_branch_id=branch_id_int)
        .select_related('shipper_profile')
        .order_by('username')
    )

    if only_available:
        shippers = shippers.filter(shipper_profile__is_available=True)

    result = []
    for s in shippers:
        try:
            profile = s.shipper_profile
            active = profile.get_active_orders_count()
            can_accept = profile.can_accept_more_orders()
        except Exception:
            active = 0
            can_accept = True

        result.append({
            'id': s.id,
            'username': s.username,
            'phone': profile.phone if 'profile' in dir() else '',
            'active_orders': active,
            'max_orders': profile.max_active_orders if 'profile' in dir() else 5,
            'can_accept': can_accept,
            'is_available': profile.is_available if 'profile' in dir() else True,
        })

    return JsonResponse(result, safe=False)

