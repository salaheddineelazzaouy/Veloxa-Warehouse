from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from apps.tenants.managers import TenantAwareManager

MOROCCAN_VAT_CHOICES = [
    (Decimal("0.20"), "20%"),
    (Decimal("0.14"), "14%"),
    (Decimal("0.10"), "10%"),
    (Decimal("0.07"), "7%"),
    (Decimal("0.00"), "0%"),
]


class Invoice(models.Model):
    invoice_ref = models.CharField(max_length=64, unique=True, db_index=True)
    order_ref = models.CharField(max_length=64, db_index=True)
    customer = models.ForeignKey(
        "crm.Customer", on_delete=models.PROTECT, null=True, blank=True
    )

    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.CharField(max_length=500, blank=True)
    customer_ice = models.CharField(max_length=15, blank=True)
    customer_identifiant_fiscal = models.CharField(max_length=30, blank=True)
    customer_taxe_professionnelle = models.CharField(max_length=30, blank=True)
    customer_registre_commerce = models.CharField(max_length=30, blank=True)

    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.20"),
        help_text="Default VAT rate applied to invoice (can be overridden per line)",
    )
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, help_text="Alias for total_ttc")
    amount_in_words = models.CharField(max_length=512, blank=True)

    payment_terms = models.CharField(
        max_length=128, default="30 jours",
        help_text="Payment terms, e.g. '30 jours', 'À réception'",
    )
    payment_due_date = models.DateField(null=True, blank=True)
    vat_exempt_notice = models.CharField(
        max_length=255, blank=True,
        help_text="Auto-populated for auto_entrepreneur or export regimes",
    )

    source = models.CharField(max_length=16, default="pos")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "finance_invoice"

    def __str__(self):
        return self.invoice_ref

    def save(self, *args, **kwargs):
        self.total = self.total_ttc
        super().save(*args, **kwargs)


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.20"),
        help_text="VAT rate for this line, e.g. 0.20 for 20%%",
    )
    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )

    objects = TenantAwareManager()

    class Meta:
        db_table = "finance_invoiceline"

    def __str__(self):
        return f"{self.invoice.invoice_ref} - {self.product.sku}"

    def save(self, *args, **kwargs):
        self.total_ht = self.qty * self.unit_price
        self.total_vat = self.total_ht * self.vat_rate
        self.total_ttc = self.total_ht + self.total_vat
        self.total = self.total_ttc
        super().save(*args, **kwargs)
