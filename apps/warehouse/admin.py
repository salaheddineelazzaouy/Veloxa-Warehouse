from django.contrib import admin
from .models import Product, StockMovement, Location, Category, Unit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "abbreviation")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "unit", "cost_price", "is_active", "created_at")
    list_filter = ("is_active", "category", "unit")
    search_fields = ("sku", "name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "qty", "type", "reference", "created_by", "created_at")
    list_filter = ("type",)
    search_fields = ("reference", "product__sku")
    readonly_fields = ("product", "qty", "type", "reference", "created_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
