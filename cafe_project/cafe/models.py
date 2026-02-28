from django.db import models
from django.contrib.gis.db import models as gis_models

# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False) #phân quyền 

    def __str__(self):
        return self.username

#loại sản phẩm
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

#tên món  
class Product(models.Model):
    name = models.CharField(max_length=100)
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
        ("bank", "Chuyển khoản"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.IntegerField(default=0)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default="cash",
    )

    def __str__(self):
        return f"Order #{self.id}"

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
    location = gis_models.PointField(srid=4326, geography=True)

    def __str__(self):
        return self.name