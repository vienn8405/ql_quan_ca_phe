# ☕ HỆ THỐNG QUẢN LÝ QUÁN CÀ PHÊ

**Django 6.0.1 + GeoDjango + PostGIS**

---

## 📖 GIỚI THIỆU

Hệ thống quản lý quán cà phê toàn diện với các tính năng:

### ✨ Tính năng chính
- 🗺️ **Quản lý chi nhánh trên bản đồ** - Hiển thị vị trí chi nhánh với Leaflet
- 📦 **Quản lý sản phẩm & menu** - Danh mục, giá, hình ảnh
- 🛒 **Quản lý đơn hàng** - Đặt hàng, thanh toán, giao hàng
- 🚚 **Quản lý shipper** - Phân công, theo dõi đơn hàng
- 📊 **Quản lý kho** - Nhập xuất, tồn kho, cảnh báo
- 💰 **Báo cáo doanh thu** - Thống kê theo ngày, tháng, chi nhánh
- 👥 **Phân quyền người dùng** - Admin, Manager, Staff, Customer
- 📱 **Responsive design** - Tương thích mobile, tablet, desktop

### 🛠️ Công nghệ sử dụng
- **Backend:** Django 6.0.1, Python 3.11
- **Database:** PostgreSQL 15 + PostGIS 3.x
- **Frontend:** Bootstrap 5, Leaflet.js
- **Others:** Pillow, openpyxl, django-cors-headers

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT

### 📋 Yêu cầu hệ thống
- Windows 10/11 (64-bit)
- RAM: 4GB+ (khuyến nghị 8GB)
- Ổ cứng: 5GB trống
- Kết nối internet

### 📚 Hướng dẫn chi tiết

**Dành cho người mới bắt đầu (không biết gì):**
👉 **[HUONG_DAN_CAI_DAT_TU_DAU.md](HUONG_DAN_CAI_DAT_TU_DAU.md)**

Hướng dẫn từng bước:
1. Cài đặt Python 3.11
2. Cài đặt PostgreSQL 15 + PostGIS
3. Cài đặt Visual Studio Code
4. Cài đặt Git
5. Tải project về máy
6. Cài đặt thư viện Python
7. Tạo database và restore backup
8. Chạy project
9. Truy cập website

### ⚡ Cài đặt nhanh (Đã có kiến thức)

#### 1. Clone project
```bash
git clone <repository_url>
cd ql_quan_ca_phe
```

#### 2. Cài đặt thư viện
```bash
cd cafe_project
pip install -r ../requirements.txt
```

#### 3. Tạo database
```sql
CREATE DATABASE cafe_db;
CREATE EXTENSION postgis;
```

#### 4. Cấu hình database
Sửa file `cafe_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cafe_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 5. Migrate database
```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 6. Chạy server
```bash
python manage.py runserver
```

Truy cập: **http://localhost:8000/**

---

## 📦 BACKUP & RESTORE DATABASE

### 📤 Backup database

**Cách 1: Dùng script tự động (Khuyến nghị)**
```bash
python backup_database.py
```
Hoặc double-click: `backup_database.bat`

**Cách 2: Dùng pg_dump**
```bash
pg_dump -U postgres -F c -b -v -f backup/cafe_db_backup.backup cafe_db
```

### 📥 Restore database

**Cách 1: Dùng pgAdmin**
1. Mở pgAdmin 4
2. Click phải vào database → Restore
3. Chọn file backup → Restore

**Cách 2: Dùng pg_restore**
```bash
pg_restore -U postgres -d cafe_db -v backup/cafe_db_backup.backup
```

**Chi tiết:** Xem file `HUONG_DAN_BACKUP_RESTORE.md`

---

## 📁 CẤU TRÚC PROJECT

```
ql_quan_ca_phe/
├── cafe_project/              # Django project chính
│   ├── cafe/                  # App chính
│   │   ├── models.py         # Database models
│   │   ├── views.py          # Views & logic
│   │   ├── urls.py           # URL routing
│   │   ├── admin.py          # Django admin
│   │   ├── templates/        # HTML templates
│   │   └── static/           # CSS, JS, images
│   ├── cafe_project/         # Settings
│   │   ├── settings.py       # Cấu hình project
│   │   ├── urls.py           # Root URLs
│   │   └── wsgi.py           # WSGI config
│   ├── media/                # User uploads
│   │   └── products/         # Hình ảnh sản phẩm
│   └── manage.py             # Django CLI
├── backup/                    # Database backups
├── auto_download_images.py   # Script tải hình sản phẩm
├── check_products.py         # Script kiểm tra sản phẩm
├── backup_database.py        # Script backup database
├── requirements.txt          # Python dependencies
├── README.md                 # File này
├── HUONG_DAN_CAI_DAT_TU_DAU.md  # Hướng dẫn chi tiết
└── HUONG_DAN_SU_DUNG_TOAN_DIEN.md  # Hướng dẫn sử dụng
```

---

## 🎯 CHỨC NĂNG CHI TIẾT

### 1. Quản lý chi nhánh
- Thêm/sửa/xóa chi nhánh
- Hiển thị trên bản đồ (Leaflet)
- Tính khoảng cách giao hàng
- Quản lý giờ mở cửa

### 2. Quản lý sản phẩm
- Danh mục sản phẩm (Categories)
- Thông tin sản phẩm (tên, giá, mô tả, hình ảnh)
- Công thức pha chế (ProductRecipe)
- Quản lý tồn kho (Inventory)

### 3. Quản lý đơn hàng
- Đặt hàng online
- Tính toán tổng tiền
- Áp dụng voucher giảm giá
- Theo dõi trạng thái đơn hàng
- Phân công shipper

### 4. Quản lý kho
- Nhập kho từ nhà cung cấp
- Xuất kho khi bán hàng
- Cảnh báo tồn kho thấp
- Lịch sử nhập xuất (StockLog)
- Import từ Excel

### 5. Quản lý nhân viên
- Thông tin nhân viên
- Phân quyền (Admin, Manager, Staff)
- Lịch làm việc
- Quản lý shipper

### 6. Báo cáo & thống kê
- Doanh thu theo ngày/tháng/năm
- Sản phẩm bán chạy
- Hiệu suất chi nhánh
- Hiệu suất nhân viên

---

## 🔐 TÀI KHOẢN MẶC ĐỊNH

**Sau khi restore backup:**

| Username | Password | Role | Mô tả |
|----------|----------|------|-------|
| admin | admin123 | Admin | Quản trị viên |
| manager1 | manager123 | Manager | Quản lý chi nhánh |
| staff1 | staff123 | Staff | Nhân viên |
| customer1 | customer123 | Customer | Khách hàng |

**Lưu ý:** Đổi mật khẩu sau khi đăng nhập lần đầu!

---

## 🌐 CÁC TRANG QUAN TRỌNG

| Trang | URL | Mô tả |
|-------|-----|-------|
| Trang chủ | http://localhost:8000/ | Trang chủ website |
| Đăng nhập | http://localhost:8000/login/ | Đăng nhập hệ thống |
| Admin | http://localhost:8000/admin/ | Django Admin |
| Menu | http://localhost:8000/menu/ | Danh sách sản phẩm |
| Bản đồ | http://localhost:8000/map/ | Chi nhánh trên bản đồ |
| Đơn hàng | http://localhost:8000/orders/ | Quản lý đơn hàng |
| Kho | http://localhost:8000/inventory/ | Quản lý kho |
| Báo cáo | http://localhost:8000/reports/ | Báo cáo doanh thu |

---

## 🛠️ SCRIPTS TIỆN ÍCH

### 1. Tải hình ảnh sản phẩm tự động
```bash
python auto_download_images.py
```
Tự động tải hình từ Unsplash cho các sản phẩm chưa có hình.

### 2. Kiểm tra sản phẩm
```bash
python check_products.py
```
Hiển thị danh sách sản phẩm và trạng thái hình ảnh.

### 3. Backup database
```bash
python backup_database.py
```
Tự động backup database với timestamp.

### 4. Menu chính (Windows)
```bash
MENU_CHINH.bat
```
Menu tổng hợp các chức năng thường dùng.

---

## 🔧 TROUBLESHOOTING

### Lỗi thường gặp

**1. "python is not recognized"**
- Python chưa được thêm vào PATH
- Giải pháp: Cài lại Python, tích "Add Python to PATH"

**2. "No module named 'django'"**
- Chưa cài thư viện
- Giải pháp: `pip install -r requirements.txt`

**3. "password authentication failed"**
- Mật khẩu database sai
- Giải pháp: Sửa `settings.py`, cập nhật PASSWORD

**4. "could not connect to server"**
- PostgreSQL chưa chạy
- Giải pháp: Mở Services, start postgresql-x64-15

**5. "Port 8000 is already in use"**
- Cổng đang được sử dụng
- Giải pháp: `python manage.py runserver 8080`

**Chi tiết:** Xem phần Troubleshooting trong `HUONG_DAN_CAI_DAT_TU_DAU.md`

---

## 📚 TÀI LIỆU THAM KHẢO

### Hướng dẫn trong project
- **HUONG_DAN_CAI_DAT_TU_DAU.md** - Hướng dẫn cài đặt chi tiết từ A-Z
- **HUONG_DAN_SU_DUNG_TOAN_DIEN.md** - Hướng dẫn sử dụng các chức năng
- **HUONG_DAN_STRIPE.md** - Tích hợp thanh toán Stripe
- **HUONG_DAN_SO_DO_TUAN_TU.md** - Sơ đồ tuần tự các chức năng

### Tài liệu bên ngoài
- **Django:** https://docs.djangoproject.com/
- **GeoDjango:** https://docs.djangoproject.com/en/stable/ref/contrib/gis/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **PostGIS:** https://postgis.net/documentation/
- **Leaflet:** https://leafletjs.com/reference.html
- **Bootstrap 5:** https://getbootstrap.com/docs/5.0/

---

## 👨‍💻 PHÁT TRIỂN

### Cấu trúc Models chính

```python
# Chi nhánh
Branch(name, address, location, phone, opening_hours, delivery_radius)

# Sản phẩm
Category(name, description)
Product(name, category, price, description, image)
ProductRecipe(product, raw_material, quantity)

# Đơn hàng
Order(customer, branch, total_price, status, order_type)
OrderItem(order, product, quantity, price)

# Kho
RawMaterial(name, unit, quantity, min_quantity)
Inventory(product, branch, quantity)
StockLog(material, branch, quantity, type, note)

# Nhân viên
Employee(user, branch, role, phone, hire_date)
ShipperProfile(employee, vehicle_type, license_plate)
```

### Thêm chức năng mới

1. Tạo model trong `cafe/models.py`
2. Tạo migration: `python manage.py makemigrations`
3. Chạy migration: `python manage.py migrate`
4. Tạo view trong `cafe/views.py`
5. Thêm URL trong `cafe/urls.py`
6. Tạo template trong `cafe/templates/`
7. Đăng ký admin trong `cafe/admin.py`

---

## 📝 CHANGELOG

### Version 1.0.0 (2026-05-06)
- ✅ Hoàn thành tất cả chức năng chính
- ✅ Tích hợp bản đồ Leaflet
- ✅ Quản lý đơn hàng và giao hàng
- ✅ Báo cáo doanh thu
- ✅ Phân quyền người dùng
- ✅ Responsive design
- ✅ Hướng dẫn cài đặt chi tiết

---

## 📞 HỖ TRỢ

### Liên hệ
- **Email:** support@cafe.com
- **GitHub:** https://github.com/username/ql_quan_ca_phe

### Báo lỗi
Nếu gặp lỗi, vui lòng:
1. Kiểm tra phần Troubleshooting
2. Xem log lỗi trong Terminal
3. Tìm kiếm lỗi trên Google
4. Tạo issue trên GitHub (nếu có)

---

## 📄 LICENSE

MIT License - Tự do sử dụng cho mục đích học tập và thương mại.

---

## 🎓 CREDITS

**Developed by:** [Tên sinh viên]  
**Instructor:** [Tên giảng viên]  
**University:** [Tên trường]  
**Year:** 2026

---

## ✅ CHECKLIST DEMO

Trước khi demo cho giảng viên:

- [ ] Database đã có dữ liệu đầy đủ
- [ ] Tất cả sản phẩm đều có hình ảnh
- [ ] Đã test tất cả chức năng chính
- [ ] Server chạy ổn định
- [ ] Đã chuẩn bị tài khoản demo
- [ ] Đã backup database
- [ ] Đã đọc kỹ hướng dẫn sử dụng
- [ ] Đã chuẩn bị câu trả lời cho các câu hỏi thường gặp

---

**🎉 Chúc bạn demo thành công!**
