from django.db import models
from apps.tenants.managers import TenantAwareManager


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "warehouse_category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Kilogram, Piece, Box")
    abbreviation = models.CharField(max_length=10, unique=True, help_text="e.g. kg, pcs, box")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouse_unit"
        ordering = ["name"]

    def __str__(self):
        return f"{self.abbreviation} ({self.name})"


class Product(models.Model):
    """No `stock` field — current stock is always derived from StockMovement SUM."""
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products",
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.PROTECT, null=True, blank=True,
        related_name="products",
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "warehouse_product"
        verbose_name = "Product"

    def __str__(self):
        return f"{self.sku} — {self.name}"
