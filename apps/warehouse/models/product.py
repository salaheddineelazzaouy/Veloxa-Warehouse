from django.db import models


class Product(models.Model):
    """No `stock` field — current stock is always derived from StockMovement SUM."""
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=16, default="pcs")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "warehouse_product"
        verbose_name = "Product"

    def __str__(self):
        return f"{self.sku} — {self.name}"
