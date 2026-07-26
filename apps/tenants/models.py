from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, blank=True, help_text="Custom domain (optional)")
    is_active = models.BooleanField(default=True)

    legal_name = models.CharField(max_length=255, blank=True, help_text="Full legal name & form, e.g. Veloxa SARL")
    address = models.CharField(max_length=500, blank=True, help_text="Registered office address (Siège Social)")
    ice = models.CharField(max_length=15, blank=True, help_text="ICE — 15-digit national company identifier")
    identifiant_fiscal = models.CharField(max_length=8, blank=True, help_text="IF — 8-digit Tax Identifier")
    registre_commerce = models.CharField(max_length=64, blank=True, help_text="RC number + city, e.g. RC 123456 Marrakech")
    taxe_professionnelle = models.CharField(max_length=64, blank=True, help_text="TP registration number")
    capital_social = models.CharField(max_length=64, blank=True, help_text="Share capital in MAD, e.g. 10,000.00 DH")
    bank_name = models.CharField(max_length=128, blank=True)
    rib = models.CharField(max_length=24, blank=True, help_text="24-digit RIB for bank transfers")
    TAX_REGIME_CHOICES = [
        ("standard", "Régime réel"),
        ("auto_entrepreneur", "Auto-Entrepreneur"),
        ("export", "Export (0% TVA)"),
    ]
    tax_regime = models.CharField(max_length=20, choices=TAX_REGIME_CHOICES, default="standard")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants_tenant"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
