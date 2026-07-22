from django.db import models
from apps.tenants.managers import TenantAwareManager


class Location(models.Model):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "warehouse_location"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"
