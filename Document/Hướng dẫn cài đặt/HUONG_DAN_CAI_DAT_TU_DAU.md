# 🚀 HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY PROJECT TỪ ĐẦU

**Dành cho người hoàn toàn mới - Không cần biết gì trước**

---

## 📋 MỤC LỤC

1. [Giới thiệu](#giới-thiệu)
2. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Tổng quan các bước](#tổng-quan-các-bước)
4. [Bước 1: Cài đặt Python](#bước-1-cài-đặt-python)
5. [Bước 2: Cài đặt PostgreSQL + PostGIS](#bước-2-cài-đặt-postgresql--postgis)
6. [Bước 3: Cài đặt OSGeo4W (GDAL/GEOS)](#bước-3-cài-đặt-osgeo4w-gdalgeos)
7. [Bước 4: Cài đặt Visual Studio Code](#bước-4-cài-đặt-visual-studio-code)
8. [Bước 5: Cài đặt Git](#bước-5-cài-đặt-git)
9. [Bước 6: Tải project về máy](#bước-6-tải-project-về-máy)
10. [Bước 7: Cài đặt thư viện Python](#bước-7-cài-đặt-thư-viện-python)
11. [Bước 8: Cấu hình settings.py](#bước-8-cấu-hình-settingspy)
12. [Bước 9: Tạo database](#bước-9-tạo-database)
13. [Bước 10: Chạy migrations và tạo dữ liệu mẫu](#bước-10-chạy-migrations-và-tạo-dữ-liệu-mẫu)
14. [Bước 11: Chạy server](#bước-11-chạy-server)
15. [Bước 12: Truy cập website](#bước-12-truy-cập-website)
16. [Troubleshooting](#troubleshooting)

---

## 🎯 GIỚI THIỆU

Project này là **Hệ thống quản lý quán cà phê** được xây dựng bằng:
- **Django 6.0.1** - Framework web Python
- **PostgreSQL 15 + PostGIS** - Database với hỗ trợ GIS
- **Leaflet** - Hiển thị bản đồ
- **Bootstrap 5** - Giao diện đẹp

**Chức năng chính:**
- Quản lý chi nhánh trên bản đồ
- Quản lý sản phẩm, menu
- Quản lý đơn hàng, giao hàng
- Quản lý kho, nhập xuất
- Báo cáo doanh thu
- Phân quyền người dùng

---

## 💻 YÊU CẦU HỆ THỐNG

- **Hệ điều hành:** Windows 10/11 (64-bit)
- **RAM:** Tối thiểu 4GB (khuyến nghị 8GB)
- **Ổ cứng:** Còn trống ít nhất 5GB
- **Kết nối internet:** Để tải phần mềm và thư viện

---

## 📝 TỔNG QUAN CÁC BƯỚC

**Thời gian ước tính: 1-2 giờ**

1. ⏱️ Cài Python (10 phút)
2. ⏱️ Cài PostgreSQL + PostGIS (15 phút)
3. ⏱️ Cài OSGeo4W (10 phút) - **QUAN TRỌNG!**
4. ⏱️ Cài VS Code (5 phút)
5. ⏱️ Cài Git (5 phút)
6. ⏱️ Tải project (5 phút)
7. ⏱️ Cài thư viện Python (10 phút)
8. ⏱️ Cấu hình settings (5 phút)
9. ⏱️ Tạo database (5 phút)
10. ⏱️ Tạo dữ liệu mẫu (5 phút)
11. ⏱️ Chạy server (2 phút)
12. ⏱️ Test website (5 phút)

---

## 📥 BƯỚC 1: CÀI ĐẶT PYTHON

### 1.1. Tải Python

1. Truy cập: https://www.python.org/downloads/
2. Click nút **"Download Python 3.11.x"** (phiên bản mới nhất)
3. File tải về: `python-3.11.x-amd64.exe`

### 1.2. Cài đặt Python

1. **Double-click** file vừa tải
2. **⚠️ QUAN TRỌNG:** Tích vào ô **"Add Python to PATH"** ở dưới cùng
3. Click **"Install Now"**
4. Đợi cài đặt hoàn tất (3-5 phút)
5. Click **"Close"**

### 1.3. Kiểm tra cài đặt

1. Nhấn **Windows + R**
2. Gõ: `cmd` và nhấn **Enter**
3. Trong cửa sổ Command Prompt, gõ:
   ```bash
   python --version
   ```
4. Nếu hiển thị `Python 3.11.x` → ✅ Thành công!

**Nếu lỗi "python is not recognized":**
- Bạn chưa tích "Add Python to PATH"
- Gỡ cài đặt Python và cài lại, nhớ tích vào ô đó

---

## 🗄️ BƯỚC 2: CÀI ĐẶT POSTGRESQL + POSTGIS

### 2.1. Tải PostgreSQL

1. Truy cập: https://www.postgresql.org/download/windows/
2. Click **"Download the installer"**
3. Chọn phiên bản **PostgreSQL 15.x** (Windows x86-64)
4. File tải về: `postgresql-15.x-windows-x64.exe`

### 2.2. Cài đặt PostgreSQL

1. **Double-click** file vừa tải
2. Click **"Next"** → **"Next"**
3. **Installation Directory:** Để mặc định `C:\Program Files\PostgreSQL\15`
4. **Select Components:** Tích tất cả
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4
   - ✅ Stack Builder
   - ✅ Command Line Tools
5. **Data Directory:** Để mặc định
6. **Password:** Nhập mật khẩu cho user `postgres`
   - **⚠️ QUAN TRỌNG:** Nhớ mật khẩu này!
   - Ví dụ: `postgres123`
   - **Ghi lại:** `Mật khẩu PostgreSQL: postgres123`
7. **Port:** Để mặc định `5432`
8. **Locale:** Để mặc định
9. Click **"Next"** → **"Next"** → **"Finish"**

### 2.3. Cài đặt PostGIS

1. Sau khi cài PostgreSQL xong, **Stack Builder** sẽ tự động mở
2. Nếu không mở, tìm và chạy **"Stack Builder"** trong Start Menu
3. Chọn **"PostgreSQL 15 on port 5432"** → **"Next"**
4. Mở mục **"Spatial Extensions"**
5. Tích vào **"PostGIS 3.x Bundle for PostgreSQL 15"**
6. Click **"Next"** → Chọn thư mục tải về → **"Next"**
7. Click **"Next"** → **"I Agree"** → **"Next"** → **"Next"**
8. Nhập mật khẩu `postgres` (mật khẩu bạn đã tạo ở bước 2.2)
9. Đợi cài đặt hoàn tất → **"Close"**

### 2.4. Kiểm tra cài đặt

1. Mở **pgAdmin 4** (tìm trong Start Menu)
2. Nhập mật khẩu master (lần đầu sẽ yêu cầu tạo)
3. Bên trái, click **"Servers"** → **"PostgreSQL 15"**
4. Nhập mật khẩu `postgres` (mật khẩu bạn đã tạo)
5. Nếu kết nối thành công → ✅ Hoàn tất!

---

## 🗺️ BƯỚC 3: CÀI ĐẶT OSGEO4W (GDAL/GEOS)

**⚠️ BƯỚC NÀY RẤT QUAN TRỌNG! GeoDjango không chạy được nếu thiếu!**

### 3.1. Tải OSGeo4W

1. Truy cập: https://trac.osgeo.org/osgeo4w/
2. Click **"OSGeo4W Network Installer"**
3. Tải file: **osgeo4w-setup.exe** (64-bit)

### 3.2. Cài đặt OSGeo4W

1. **Double-click** file `osgeo4w-setup.exe`
2. Chọn **"Express Install"** (Cài đặt nhanh)
3. Click **"Next"**
4. Tích vào:
   - ✅ **GDAL**
   - ✅ **GEOS**
   - ✅ **PROJ**
5. **Installation Directory:** Để mặc định `C:\OSGeo4W64\`
   - **⚠️ GHI NHỚ ĐƯỜNG DẪN NÀY!**
6. Click **"Next"** → **"Install"**
7. Đợi cài đặt hoàn tất (5-10 phút)
8. Click **"Finish"**

### 3.3. Kiểm tra cài đặt

1. Mở File Explorer
2. Vào thư mục: `C:\OSGeo4W64\bin\`
3. Kiểm tra có các file sau:
   - ✅ `gdal312.dll` (hoặc `gdal38.dll`, `gdal39.dll`)
   - ✅ `geos_c.dll`
4. Nếu có → ✅ Thành công!

**Chi tiết:** Xem file `HUONG_DAN_CAI_OSGEO4W.md` nếu gặp vấn đề

---

## 📝 BƯỚC 4: CÀI ĐẶT VISUAL STUDIO CODE

### 4.1. Tải VS Code

1. Truy cập: https://code.visualstudio.com/
2. Click **"Download for Windows"**
3. File tải về: `VSCodeUserSetup-x64-x.xx.x.exe`

### 4.2. Cài đặt VS Code

1. **Double-click** file vừa tải
2. Click **"I accept the agreement"** → **"Next"**
3. **Destination Location:** Để mặc định → **"Next"**
4. **Select Start Menu Folder:** Để mặc định → **"Next"**
5. **Select Additional Tasks:** Tích tất cả các ô:
   - ✅ Add "Open with Code" action to Windows Explorer file context menu
   - ✅ Add "Open with Code" action to Windows Explorer directory context menu
   - ✅ Register Code as an editor for supported file types
   - ✅ Add to PATH
6. Click **"Next"** → **"Install"**
7. Đợi cài đặt hoàn tất → **"Finish"**

### 4.3. Cài đặt Extension cho Python

1. Mở **VS Code**
2. Nhấn **Ctrl + Shift + X** (mở Extensions)
3. Tìm và cài đặt:
   - **Python** (by Microsoft) - Click **"Install"**
   - **Pylance** (by Microsoft) - Click **"Install"**
   - **Django** (by Baptiste Darthenay) - Click **"Install"**

---

## 🔧 BƯỚC 5: CÀI ĐẶT GIT

### 5.1. Tải Git

1. Truy cập: https://git-scm.com/download/win
2. Click **"64-bit Git for Windows Setup"**
3. File tải về: `Git-x.xx.x-64-bit.exe`

### 5.2. Cài đặt Git

1. **Double-click** file vừa tải
2. Click **"Next"** nhiều lần (để mặc định tất cả)
3. **Choosing the default editor:** Chọn **"Use Visual Studio Code as Git's default editor"**
4. Tiếp tục click **"Next"** cho đến khi **"Install"**
5. Đợi cài đặt hoàn tất → **"Finish"**

### 5.3. Kiểm tra cài đặt

1. Mở **Command Prompt** (Windows + R → gõ `cmd`)
2. Gõ:
   ```bash
   git --version
   ```
3. Nếu hiển thị `git version x.xx.x` → ✅ Thành công!

---

## 📦 BƯỚC 6: TẢI PROJECT VỀ MÁY

### Cách 1: Tải từ file ZIP (Đơn giản nhất)

1. Nếu bạn có file ZIP của project (ví dụ: `ql_quan_ca_phe.zip`)
2. **Click phải** vào file ZIP → **"Extract All..."**
3. Chọn thư mục giải nén (ví dụ: `D:\Projects\`)
4. Click **"Extract"**
5. Bạn sẽ có thư mục: `D:\Projects\ql_quan_ca_phe\`

### Cách 2: Clone từ Git (Nếu có repository)

1. Mở **Command Prompt**
2. Di chuyển đến thư mục muốn lưu project:
   ```bash
   cd D:\Projects
   ```
3. Clone project:
   ```bash
   git clone <URL_REPOSITORY>
   ```

**Từ giờ, mình sẽ giả sử project ở: `D:\Projects\ql_quan_ca_phe\`**

---

## 📚 BƯỚC 7: CÀI ĐẶT THƯ VIỆN PYTHON

### 7.1. Mở project trong VS Code

1. Mở **VS Code**
2. Click **"File"** → **"Open Folder..."**
3. Chọn thư mục project: `D:\Projects\ql_quan_ca_phe`
4. Click **"Select Folder"**

### 7.2. Mở Terminal trong VS Code

1. Trong VS Code, nhấn **Ctrl + `** (phím backtick, bên trái số 1)
2. Hoặc click **"Terminal"** → **"New Terminal"**
3. Terminal sẽ mở ở dưới cùng

### 7.3. Cài đặt thư viện

1. Trong Terminal, gõ:
   ```bash
   pip install -r requirements.txt
   ```
2. Đợi cài đặt hoàn tất (5-10 phút)

**Các thư viện sẽ được cài:**
- Django 6.0.1
- psycopg2-binary (kết nối PostgreSQL)
- Pillow (xử lý ảnh)
- openpyxl (đọc file Excel)
- reportlab (tạo PDF)
- requests (HTTP requests)
- python-dotenv (environment variables)

### 7.4. Kiểm tra cài đặt

Gõ:
```bash
python -m django --version
```
Nếu hiển thị `6.0.1` → ✅ Thành công!

---

## ⚙️ BƯỚC 8: CẤU HÌNH SETTINGS.PY

### 8.1. Mở file settings.py

1. Trong VS Code, mở file: `cafe_project/cafe_project/settings.py`
2. Tìm phần đầu file (dòng 17-18)

### 8.2. Cập nhật đường dẫn GDAL/GEOS

Sửa đường dẫn cho phù hợp với máy bạn:

```python
# --- GeoDjango: GDAL/GEOS DLL paths (Windows) ---
GDAL_LIBRARY_PATH = r"C:\OSGeo4W64\bin\gdal312.dll"
GEOS_LIBRARY_PATH = r"C:\OSGeo4W64\bin\geos_c.dll"
```

**Lưu ý:**
- Nếu bạn cài OSGeo4W ở thư mục khác, sửa đường dẫn
- Nếu file DLL có tên khác (ví dụ: `gdal38.dll`), sửa tên file

### 8.3. Cập nhật thông tin database

Tìm phần `DATABASES` (dòng 88-97):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'ql_quan_cafe',
        'USER': 'postgres',
        'PASSWORD': 'postgres123',  # Mật khẩu bạn đã tạo ở Bước 2.2
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**Sửa `PASSWORD` thành mật khẩu bạn đã tạo!**

### 8.4. Lưu file

Nhấn **Ctrl + S** để lưu file

---

## 🗃️ BƯỚC 9: TẠO DATABASE

### 9.1. Tạo database mới

1. Mở **pgAdmin 4**
2. Kết nối đến **PostgreSQL 15** (nhập mật khẩu `postgres`)
3. Click phải vào **"Databases"** → **"Create"** → **"Database..."**
4. **Database name:** `ql_quan_cafe` (⚠️ Đúng tên này!)
5. **Owner:** `postgres`
6. Click **"Save"**

### 9.2. Kích hoạt PostGIS extension

1. Click phải vào database **"ql_quan_cafe"** vừa tạo
2. Chọn **"Query Tool"**
3. Trong cửa sổ Query, gõ:
   ```sql
   CREATE EXTENSION postgis;
   ```
4. Click nút **"Execute"** (biểu tượng ▶️) hoặc nhấn **F5**
5. Nếu thành công, sẽ hiển thị "CREATE EXTENSION"

---

## 🎨 BƯỚC 10: CHẠY MIGRATIONS VÀ TẠO DỮ LIỆU MẪU

### 10.1. Chạy migrations

Trong Terminal của VS Code:

```bash
cd cafe_project
python manage.py makemigrations
python manage.py migrate
```

Đợi đến khi hiển thị "Applying migrations... OK"

### 10.2. Tạo superuser (Admin)

```bash
python manage.py createsuperuser
```

Nhập thông tin:
- **Username:** `admin`
- **Email:** `admin@cafe.com` (hoặc để trống)
- **Password:** `admin123` (nhập 2 lần)

**⚠️ Ghi nhớ:** Username: `admin`, Password: `admin123`

### 10.3. Tạo dữ liệu mẫu (Optional)

Nếu có file `create_sample_data.py`:

```bash
python create_sample_data.py
```

Nếu không có, bạn có thể thêm dữ liệu thủ công qua Django Admin sau.

---

## ▶️ BƯỚC 11: CHẠY SERVER

### 11.1. Chạy server

Trong Terminal:

```bash
python manage.py runserver
```

**Kết quả:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
May 06, 2026 - 10:00:00
Django version 6.0.1, using settings 'cafe_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**✅ Server đang chạy!**

---

## 🌐 BƯỚC 12: TRUY CẬP WEBSITE

### 12.1. Mở trình duyệt

1. Mở **Google Chrome** hoặc **Microsoft Edge**
2. Truy cập: **http://localhost:8000/**

### 12.2. Đăng nhập

1. Click **"Đăng nhập"** hoặc truy cập: http://localhost:8000/login/
2. Nhập:
   - **Username:** `admin`
   - **Password:** `admin123`
3. Click **"Đăng nhập"**

### 12.3. Truy cập Django Admin

1. Truy cập: **http://localhost:8000/admin/**
2. Đăng nhập với tài khoản admin
3. Bạn có thể thêm dữ liệu mẫu tại đây

### 12.4. Các trang quan trọng

| Trang | URL |
|-------|-----|
| Trang chủ | http://localhost:8000/ |
| Đăng nhập | http://localhost:8000/login/ |
| Admin | http://localhost:8000/admin/ |
| Menu | http://localhost:8000/menu/ |
| Bản đồ | http://localhost:8000/map/ |

---

## 🔧 TROUBLESHOOTING

### Lỗi 1: "python is not recognized"

**Nguyên nhân:** Python chưa được thêm vào PATH

**Giải pháp:**
1. Gỡ cài đặt Python
2. Cài lại và **nhớ tích** "Add Python to PATH"

---

### Lỗi 2: "No module named 'django'"

**Nguyên nhân:** Chưa cài đặt thư viện

**Giải pháp:**
```bash
pip install -r requirements.txt
```

---

### Lỗi 3: "Could not find the GDAL library"

**Nguyên nhân:** OSGeo4W chưa cài hoặc đường dẫn sai

**Giải pháp:**
1. Kiểm tra file DLL có tồn tại: `C:\OSGeo4W64\bin\gdal312.dll`
2. Nếu không có, cài lại OSGeo4W (Bước 3)
3. Nếu có, sửa đường dẫn trong `settings.py`
4. Xem chi tiết: `HUONG_DAN_CAI_OSGEO4W.md`

---

### Lỗi 4: "password authentication failed for user 'postgres'"

**Nguyên nhân:** Mật khẩu database sai

**Giải pháp:**
1. Mở file `settings.py`
2. Sửa `PASSWORD` trong `DATABASES` thành mật khẩu đúng

---

### Lỗi 5: "could not connect to server"

**Nguyên nhân:** PostgreSQL chưa chạy

**Giải pháp:**
1. Mở **Services** (Windows + R → gõ `services.msc`)
2. Tìm **"postgresql-x64-15"**
3. Click phải → **"Start"**

---

### Lỗi 6: "database 'ql_quan_cafe' does not exist"

**Nguyên nhân:** Chưa tạo database

**Giải pháp:**
1. Mở pgAdmin 4
2. Tạo database tên `ql_quan_cafe` (Bước 9)

---

### Lỗi 7: "Port 8000 is already in use"

**Nguyên nhân:** Cổng 8000 đang được sử dụng

**Giải pháp:**
Chạy server trên cổng khác:
```bash
python manage.py runserver 8080
```
Truy cập: http://localhost:8080/

---

### Lỗi 8: "ModuleNotFoundError: No module named 'psycopg2'"

**Nguyên nhân:** Thư viện psycopg2 chưa cài

**Giải pháp:**
```bash
pip install psycopg2-binary
```

---

## 📞 HỖ TRỢ THÊM

### Kiểm tra phiên bản

```bash
# Python
python --version

# Django
python -m django --version

# PostgreSQL
psql --version

# Git
git --version
```

### Xem log lỗi

Khi chạy server, nếu có lỗi, log sẽ hiển thị trong Terminal. Copy log và tìm kiếm trên Google.

### Tắt server

Trong Terminal đang chạy server, nhấn **Ctrl + C**

---

## ✅ CHECKLIST HOÀN THÀNH

- [ ] Đã cài đặt Python 3.11
- [ ] Đã cài đặt PostgreSQL 15 + PostGIS
- [ ] Đã cài đặt OSGeo4W (GDAL/GEOS)
- [ ] Đã cài đặt Visual Studio Code
- [ ] Đã cài đặt Git
- [ ] Đã tải project về máy
- [ ] Đã cài đặt thư viện Python
- [ ] Đã cấu hình settings.py (GDAL/GEOS, DATABASE)
- [ ] Đã tạo database `ql_quan_cafe`
- [ ] Đã kích hoạt PostGIS extension
- [ ] Đã chạy migrations
- [ ] Đã tạo superuser
- [ ] Đã chạy server thành công
- [ ] Đã truy cập được website
- [ ] Đã đăng nhập được

---

## 🎉 HOÀN THÀNH!

Chúc mừng! Bạn đã cài đặt và chạy thành công project.

**Bước tiếp theo:**
1. Thêm dữ liệu mẫu qua Django Admin
2. Khám phá các chức năng
3. Test các tính năng
4. Chuẩn bị demo cho giảng viên

**Tài liệu tham khảo:**
- `README.md` - Tổng quan project
- `HUONG_DAN_CAI_OSGEO4W.md` - Chi tiết cài GDAL/GEOS
- `HUONG_DAN_SU_DUNG_TOAN_DIEN.md` - Hướng dẫn sử dụng

**Chúc bạn thành công! 🚀**
