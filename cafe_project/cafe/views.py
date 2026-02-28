from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Product, Order, Category, Inventory, Employee, OrderItem
from django.http import HttpResponse
from django.utils import timezone
from django.core.serializers import serialize
from .models import CafeBranch
from django.http import JsonResponse
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D


# Create your views here.
def home(request):
    products = Product.objects.all()
    return render(request, 'cafe/home.html', {
        'products': products
    })



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = User.objects.filter(
            username=username,
            password=password,
            is_admin=True
        ).first()

        if user:
            request.session['admin_id'] = user.id
            return redirect('admin_dashboard')

    return render(request, 'cafe/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('home')


def admin_dashboard(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    return render(request, 'cafe/admin_dashboard.html')

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
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        lat = request.POST.get('lat', '').strip()
        lng = request.POST.get('lng', '').strip()

        # validate đơn giản
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return render(request, 'cafe/branch_add.html', {
                'error': 'Tọa độ không hợp lệ. Nhập số nhé (vd: 10.12345).',
                'name': name, 'address': address, 'lat': lat, 'lng': lng,
            })

        CafeBranch.objects.create(
            name=name,
            address=address,
            location=Point(lng_f, lat_f, srid=4326)  # nhớ: Point(lng, lat)
        )
        return redirect('branch_list')

    return render(request, 'cafe/branch_add.html')


def branch_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    b = CafeBranch.objects.get(id=id)

    if request.method == 'POST':
        b.name = request.POST.get('name', '').strip()
        b.address = request.POST.get('address', '').strip()

        lat = request.POST.get('lat', '').strip()
        lng = request.POST.get('lng', '').strip()

        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return render(request, 'cafe/branch_edit.html', {
                'error': 'Tọa độ không hợp lệ.',
                'b': b,
                'lat': lat, 'lng': lng
            })

        b.location = Point(lng_f, lat_f, srid=4326)
        b.save()
        return redirect('branch_list')

    # đổ sẵn lat/lng từ PointField (POINT (lng lat))
    return render(request, 'cafe/branch_edit.html', {
        'b': b,
        'lat': b.location.y if b.location else '',
        'lng': b.location.x if b.location else '',
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

    products = Product.objects.all()
    return render(request, 'cafe/product_list.html', {
        'products': products
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

         # lấy file ảnh 
        img = request.FILES.get('image')
     
    #tạo sản phẩm
        product = Product.objects.create(
            name=name,
            price=price,
            category=Category.objects.get(id=category_id)
        )

    #tạo kho tương ứng (QUAN TRỌNG)
        Inventory.objects.create(
            product=product,
            quantity=0
        )
        return redirect('product_list')

    return render(request, 'cafe/product_add.html', {
        'categories': categories
    })

#xóa sản phẩm
def product_delete(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    Product.objects.filter(id=id).delete()
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

    orders = Order.objects.all().prefetch_related('orderitem_set')

    for o in orders:
        items = OrderItem.objects.filter(order=o)
        o.total_price = sum(
            item.price * item.quantity
            for item in items
        )

    return render(request, 'cafe/order_list.html', {
        'orders': orders
    })

#Tạo đơn hàng
def order_add(request):
    if 'admin_id' not in request.session:
        return redirect('login')

    products = Product.objects.all()

    if request.method == 'POST':
        product_id = request.POST['product']
        quantity = int(request.POST['quantity'])

        product = Product.objects.get(id=product_id)
        inventory = Inventory.objects.get(product=product)

        if inventory.quantity < quantity:
            return HttpResponse("❌ Không đủ hàng trong kho")

        # 1️⃣ tạo order (KHÔNG có product, quantity)
        order = Order.objects.create(
            payment_method='cash'
        )

        # 2️⃣ tạo order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        # 3️⃣ cập nhật tổng tiền
        order.total_price = product.price * quantity
        order.save()

        # 4️⃣ trừ kho
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

    Order.objects.filter(id=id).delete()
    return redirect('order_list')

 #sửa đơn hàng
def order_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    order = Order.objects.get(id=id)
    items = OrderItem.objects.filter(order=order)
    products = Product.objects.all()

    if request.method == 'POST':
        item = items.first()  # tạm sửa 1 món
        item.product_id = request.POST['product']
        item.quantity = int(request.POST['quantity'])
        item.price = item.product.price
        item.save()

        order.total_price = item.price * item.quantity
        order.save()
        return redirect('order_list')

    return render(request, 'cafe/order_edit.html', {
        'order': order,
        'items': items,
        'products': products
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

    inventories = Inventory.objects.select_related('product')

    return render(request, 'cafe/inventory_list.html', {
        'inventories': inventories
    })

#nhập / xuất kho
def inventory_edit(request, id):
    if 'admin_id' not in request.session:
        return redirect('login')

    inventory = Inventory.objects.get(id=id)

    if request.method == 'POST':
        inventory.quantity = request.POST['quantity']
        inventory.save()
        return redirect('inventory_list')

    return render(request, 'cafe/inventory_edit.html', {
        'inventory': inventory
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
    return render(request, 'cafe/user_menu.html', {
        'products': products
    })
#xem giỏ hàng
def cart(request):
    cart = request.session.get('cart', {})

    total = 0
    for item in cart.values():
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']

    return render(request, 'cafe/cart.html', {
        'cart': cart,
        'total': total
    })



def user_order_create(request):
    cart = request.session.get('cart')

    if not cart:
        return redirect('cart')

    #Tạo đơn hàng
    order = Order.objects.create(
        total_price=0,
        created_at=timezone.now()
    )

    total = 0

    #Tạo từng OrderItem
    for pid, item in cart.items():
        product = Product.objects.get(id=pid)
        quantity = item['quantity']
        price = item['price']

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=price
        )

        total += price * quantity

        #Trừ kho
        inventory = Inventory.objects.get(product=product)
        inventory.quantity -= quantity
        inventory.save()

    #Cập nhật tổng tiền
    order.total_price = total
    order.save()

    # lưu order_id vào session
    request.session["last_order_id"] = order.id

    #Xóa giỏ hàng
    request.session['cart'] = {}

    return render(request, 'cafe/order_success.html', {
        'order': order
    })

#thêm vào giỏ
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    pid = str(product_id)

    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {
            'name': product.name,
            'price': int(product.price),
            'quantity': 1
        }

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')

#thêm hoặc giảm số lượng sản phẩm
def cart_update(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    action = request.GET.get('action')

    if pid in cart:
        if action == 'increase':
            cart[pid]['quantity'] += 1
        elif action == 'decrease':
            cart[pid]['quantity'] -= 1
            if cart[pid]['quantity'] <= 0:
                del cart[pid]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')

#xóa sản phẩm khỏi giỏ
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)

    if pid in cart:
        del cart[pid]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')

#view xem đon hàng
def user_order_detail(request):
    order_id = request.session.get("last_order_id")

    if not order_id:
        return render(request, "cafe/order_empty.html")

    order = Order.objects.get(id=order_id)
    items = order.items.all()  # related_name="items"

    return render(request, "cafe/order_detail.html", {
        "order": order,
        "items": items,
    })
#tool1 view bản đồ
def map_view(request):
    return render(request, "cafe/map.html")
#tool1 Trả về danh sách chi nhánh dạng GeoJSON tự tạo
def branches_geojson(request):
    branches = CafeBranch.objects.all()

    features = []

    for branch in branches:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                # GeoJSON yêu cầu [longitude, latitude]
                "coordinates": [
                    branch.location.x,
                    branch.location.y
                ]
            },
            "properties": {
                "id": branch.id,
                "name": branch.name,
                "address": branch.address,
            }
        }
        features.append(feature)

    data = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(data)


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
            "lat": cafe.location.y,
            "lng": cafe.location.x,
            "distance": round(cafe.distance.m, 1),
        })

    return JsonResponse(result, safe=False)