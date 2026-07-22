from django.db import models
from django.contrib.auth import get_user_model
from apps.tenants.managers import TenantAwareManager


class StockMovement(models.Model):
    """THE immutable ledger — every stock change is one row.

    - `qty` is signed: positive = inbound, negative = outbound
    - Once created, entries CANNOT be updated or deleted.
    - Corrections are made via new adjustment entries.
    """
    class Type(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"
        ADJUSTMENT = "adjustment", "Adjustment"

    product = models.ForeignKey(
        "warehouse.Product",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    qty = models.IntegerField()
    type = models.CharField(max_length=16, choices=Type.choices, db_index=True)
    reference = models.CharField(max_length=64, db_index=True)
    note = models.TextField(blank=True)
    location = models.ForeignKey(
        "warehouse.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "warehouse_stockmovement"
        verbose_name = "Stock Movement"
        ordering = ["-created_at"]
        permissions = [
            ("add_adjustment", "Can add stock adjustment"),
        ]
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["reference"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise NotImplementedError("Stock movements cannot be updated")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Stock movements are immutable")

    def __str__(self):
        return f"{self.type} {self.qty:+d} — {self.product.sku} ({self.reference})"
