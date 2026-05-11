# 🗺️ HƯỚNG DẪN CÀI ĐẶT OSGEO4W (GDAL/GEOS)

**Bắt buộc cho GeoDjango trên Windows**

---

## 🎯 OSGEO4W LÀ GÌ?

OSGeo4W là bộ công cụ GIS cho Windows, bao gồm:
- **GDAL** - Thư viện xử lý dữ liệu địa lý
- **GEOS** - Thư viện tính toán hình học
- **PROJ** - Thư viện chuyển đổi tọa độ

**GeoDjango cần các thư viện này để hoạt động!**

---

## 📥 CÁCH 1: CÀI ĐẶT OSGEO4W (KHUYẾN NGHỊ)

### Bước 1: Tải OSGeo4W

1. Truy cập: https://trac.osgeo.org/osgeo4w/
2. Click **"OSGeo4W Network Installer"**
3. Tải file: **osgeo4w-setup.exe** (64-bit)

### Bước 2: Chạy Installer

1. **Double-click** file `osgeo4w-setup.exe`
2. Chọn **"Express Install"** (Cài đặt nhanh)
3. Click **"Next"**

### Bước 3: Chọn Packages

Tích vào các package sau:
- ✅ **GDAL** - Geospatial Data Abstraction Library
- ✅ **GEOS** - Geometry Engine Open Source
- ✅ **PROJ** - Cartographic Projections Library
- ✅ **QGIS** (Optional - nếu muốn có công cụ GIS)

Click **"Next"**

### Bước 4: Chọn Thư Mục Cài Đặt

**QUAN TRỌNG:** Ghi nhớ đường dẫn cài đặt!

- **Mặc định:** `C:\OSGeo4W64\`
- **Hoặc:** `C:\Program Files\OSGeo4W\`

Click **"Next"** → **"Install"**

### Bước 5: Đợi Cài Đặt

- Quá trình cài đặt mất 5-10 phút
- Sẽ tải và cài đặt các package
- Đợi đến khi hiển thị "Installation Complete"
- Click **"Finish"**

---

## 🔧 CÁCH 2: CÀI ĐẶT THỦ CÔNG (NẾU CÁCH 1 KHÔNG ĐƯỢC)

### Bước 1: Tải GDAL Binary

1. Truy cập: https://www.gisinternals.com/release.php
2. Chọn phiên bản phù hợp:
   - **MSVC 2022** (x64)
   - **GDAL 3.x** (stable)
3. Tải file: `gdal-3xx-xxxx-x64-core.msi`

### Bước 2: Cài Đặt GDAL

1. **Double-click** file .msi vừa tải
2. Click **"Next"** → **"Next"**
3. **Installation Directory:** Ghi nhớ đường dẫn (ví dụ: `C:\Program Files\GDAL\`)
4. Click **"Install"** → **"Finish"**

### Bước 3: Thêm vào PATH

1. Nhấn **Windows + R**
2. Gõ: `sysdm.cpl` → **Enter**
3. Tab **"Advanced"** → Click **"Environment Variables"**
4. Trong **"System variables"**, tìm **"Path"**
5. Click **"Edit"** → **"New"**
6. Thêm đường dẫn: `C:\Program Files\GDAL\bin`
7. Click **"OK"** → **"OK"** → **"OK"**

---

## ⚙️ CẤU HÌNH DJANGO SETTINGS

### Bước 1: Tìm Đường Dẫn DLL

**Nếu cài OSGeo4W:**
```
C:\OSGeo4W64\bin\gdal312.dll
C:\OSGeo4W64\bin\geos_c.dll
```

**Nếu cài GDAL thủ công:**
```
C:\Program Files\GDAL\bin\gdal312.dll
C:\Program Files\GDAL\bin\geos_c.dll
```

### Bước 2: Cập Nhật settings.py

Mở file `cafe_project/cafe_project/settings.py`

Tìm phần đầu file và sửa đường dẫn:

```python
# --- GeoDjango: GDAL/GEOS DLL paths (Windows) ---
GDAL_LIBRARY_PATH = r"C:\OSGeo4W64\bin\gdal312.dll"
GEOS_LIBRARY_PATH = r"C:\OSGeo4W64\bin\geos_c.dll"

os.environ["GDAL_LIBRARY_PATH"] = GDAL_LIBRARY_PATH
os.environ["GEOS_LIBRARY_PATH"] = GEOS_LIBRARY_PATH
# --- end GeoDjango ---
```

**Lưu ý:** Thay đổi đường dẫn cho phù hợp với máy bạn!

---

## ✅ KIỂM TRA CÀI ĐẶT

### Cách 1: Kiểm tra trong Python

1. Mở **Command Prompt**
2. Gõ:
   ```bash
   python
   ```
3. Trong Python shell, gõ:
   ```python
   from django.contrib.gis import gdal
   print(gdal.HAS_GDAL)
   ```
4. Nếu hiển thị `True` → Thành công!

### Cách 2: Kiểm tra trong Django

1. Trong Terminal của VS Code:
   ```bash
   cd cafe_project
   python manage.py shell
   ```
2. Trong Django shell:
   ```python
   from django.contrib.gis.geos import Point
   p = Point(106.7, 10.8)
   print(p)
   ```
3. Nếu hiển thị `POINT (106.7 10.8)` → Thành công!

---

## 🚨 TROUBLESHOOTING

### Lỗi 1: "Could not find the GDAL library"

**Nguyên nhân:** Django không tìm thấy file DLL

**Giải pháp:**
1. Kiểm tra file DLL có tồn tại không:
   - Mở File Explorer
   - Vào `C:\OSGeo4W64\bin\`
   - Tìm file `gdal312.dll` và `geos_c.dll`

2. Nếu không có, cài lại OSGeo4W

3. Nếu có, sửa đường dẫn trong `settings.py`

---

### Lỗi 2: "OSError: [WinError 126]"

**Nguyên nhân:** Thiếu dependencies

**Giải pháp:**
1. Cài đặt **Visual C++ Redistributable**:
   - Truy cập: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Tải và cài đặt

2. Restart máy tính

3. Thử lại

---

### Lỗi 3: "GDAL version mismatch"

**Nguyên nhân:** Phiên bản GDAL không khớp

**Giải pháp:**
1. Kiểm tra phiên bản GDAL:
   ```bash
   gdalinfo --version
   ```

2. Cập nhật đường dẫn DLL trong `settings.py`:
   - Nếu GDAL 3.8: `gdal38.dll`
   - Nếu GDAL 3.9: `gdal39.dll`
   - Nếu GDAL 3.12: `gdal312.dll`

---

### Lỗi 4: "ImportError: DLL load failed"

**Nguyên nhân:** PATH chưa đúng

**Giải pháp:**
1. Thêm OSGeo4W vào PATH:
   - Mở Environment Variables
   - Thêm: `C:\OSGeo4W64\bin`
   - Restart Command Prompt

2. Hoặc thêm vào đầu `settings.py`:
   ```python
   import os
   os.environ['PATH'] = r'C:\OSGeo4W64\bin;' + os.environ['PATH']
   ```

---

## 📝 GHI CHÚ QUAN TRỌNG

### 1. Đường dẫn phải dùng raw string
```python
# ✅ Đúng
GDAL_LIBRARY_PATH = r"C:\OSGeo4W64\bin\gdal312.dll"

# ❌ Sai
GDAL_LIBRARY_PATH = "C:\OSGeo4W64\bin\gdal312.dll"
```

### 2. Phiên bản DLL phải khớp
- Kiểm tra file DLL thực tế trong thư mục `bin`
- Tên file có thể là: `gdal38.dll`, `gdal39.dll`, `gdal312.dll`
- Cập nhật tên file cho đúng trong `settings.py`

### 3. Cần restart sau khi cài
- Restart Command Prompt
- Restart VS Code
- Hoặc restart máy tính

---

## 🎓 TÓM TẮT

**Các bước cần làm:**
1. ✅ Cài OSGeo4W (hoặc GDAL thủ công)
2. ✅ Tìm đường dẫn file DLL
3. ✅ Cập nhật `settings.py`
4. ✅ Kiểm tra cài đặt
5. ✅ Nếu lỗi, xem phần Troubleshooting

**Sau khi hoàn thành, bạn có thể tiếp tục với các bước tiếp theo trong HUONG_DAN_CAI_DAT_TU_DAU.md**

---

**Chúc bạn cài đặt thành công! 🎉**
