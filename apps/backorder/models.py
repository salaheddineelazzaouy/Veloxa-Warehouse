from django.db import models
from django.contrib.auth import get_user_model


class BackOrder(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIALLY_FULFILLED = "partially_fulfilled", "Partially Fulfilled"
        CLOSED = "closed", "Closed"

    product = models.ForeignKey(
        "warehouse.Product",
        on_delete=models.PROTECT,
        related_name="backorders",
    )
    qty = models.PositiveIntegerField()
    qty_fulfilled = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    sales_order_ref = models.CharField(max_length=64, db_index=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "backorder_backorder"
        ordering = ["-created_at"]

    @property
    def qty_remaining(self) -> int:
        return self.qty - self.qty_fulfilled

    def __str__(self):
        return f"BO-{self.id} {self.product.sku} x{self.qty}"
