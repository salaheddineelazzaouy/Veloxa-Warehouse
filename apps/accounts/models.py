from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("warehouse_manager", "Warehouse Manager"),
        ("auditor", "Auditor"),
        ("viewer", "Read-Only Viewer"),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="viewer")
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email or self.username
