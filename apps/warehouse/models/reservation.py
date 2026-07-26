from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.tenants.managers import TenantAwareManager


class StockReservation(models.Model):
    """Allocates available stock to a pending order before shipment.

    Reservations reduce available stock without creating movements.
    Only confirmed reservations create outbound StockMovement entries.
    Expired or released reservations return stock to the available pool.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FULFILLED = "fulfilled", "Fulfilled"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"

    product = models.ForeignKey(
        "warehouse.Product",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    qty = models.PositiveIntegerField()
    order_ref = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Auto-release after this time")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "warehouse_stockreservation"
        verbose_name = "Stock Reservation"
        verbose_name_plural = "Stock Reservations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "status"]),
            models.Index(fields=["order_ref", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(qty__gt=0),
                name="reservation_qty_positive",
            ),
        ]

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"RES-{self.id} {self.product.sku} x{self.qty} [{self.status}]"
