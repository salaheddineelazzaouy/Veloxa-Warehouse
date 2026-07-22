from django.db import models
from apps.tenants.managers import TenantAwareManager


class Customer(models.Model):
    objects = TenantAwareManager()
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='customers'
    )

    name = models.CharField(max_length=255)
    ice = models.CharField(
        max_length=15,
        blank=True,
        help_text="ICE (Identifiant Commun de l'Entreprise) — exactly 15 digits"
    )
    identifiant_fiscal = models.CharField(
        max_length=30, blank=True,
        help_text="IF (Identifiant Fiscal) for tax reporting"
    )
    taxe_professionnelle = models.CharField(
        max_length=30, blank=True,
        help_text="TP (Taxe Professionnelle) for commercial documentation"
    )
    registre_commerce = models.CharField(
        max_length=30, blank=True,
        help_text="RC (Registre de Commerce) for legal entity verification"
    )

    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)

    is_active = models.BooleanField(default=True)
    is_anonymized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "crm_customer"
        ordering = ["-created_at"]
        unique_together = ('tenant', 'name')
        indexes = [
            models.Index(fields=['tenant', 'name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
