from django.contrib import admin
from .models import CafeBranch

# Register your models here.
#tool1 
@admin.register(CafeBranch)
class CafeBranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address")