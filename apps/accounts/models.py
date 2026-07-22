from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class TenantAwareUserManager(UserManager):
    def get_queryset(self):
        from apps.tenants.utils import get_current_tenant_id
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            return qs.filter(tenant_id=tenant_id)
        return qs


class User(AbstractUser):
    objects = TenantAwareUserManager()
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("warehouse_manager", "Warehouse Manager"),
        ("auditor", "Auditor"),
        ("viewer", "Read-Only Viewer"),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="viewer")
    phone = models.CharField(max_length=20, blank=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="users",
    )

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email or self.username
