from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from apps.tenants.managers import TenantAwareManager
from apps.finance.number_to_french import number_to_french


def _next_ref(prefix, model_class, year=None):
    from django.utils import timezone
    if year is None:
        year = timezone.now().year
    tag = f"{prefix}-{year}-"
    last = model_class.objects.filter(ref__startswith=tag).order_by("-ref").values_list("ref", flat=True).first()
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{tag}{seq:03d}"


# ────────────────────── Devis (Quote) ──────────────────────

class Quote(models.Model):
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("sent", "Envoyé"),
        ("accepted", "Accepté"),
        ("rejected", "Refusé"),
        ("expired", "Expiré"),
    ]
    ref = models.CharField(max_length=64, unique=True, db_index=True)
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.CharField(max_length=500, blank=True)
    customer_ice = models.CharField(max_length=15, blank=True)
    customer_identifiant_fiscal = models.CharField(max_length=30, blank=True)
    customer_registre_commerce = models.CharField(max_length=30, blank=True)
    customer_taxe_professionnelle = models.CharField(max_length=30, blank=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    validity_days = models.IntegerField(default=30, help_text="Durée de validité en jours")
    payment_terms = models.CharField(max_length=128, default="30 jours")
    notes = models.TextField(blank=True)

    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.20"))
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_in_words = models.CharField(max_length=512, blank=True)
    vat_exempt_notice = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_quote"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = _next_ref("DEV", Quote)
        super().save(*args, **kwargs)


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.20"))
    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_quoteline"

    def save(self, *args, **kwargs):
        self.total_ht = self.qty * self.unit_price
        self.total_vat = self.total_ht * self.vat_rate
        self.total_ttc = self.total_ht + self.total_vat
        super().save(*args, **kwargs)


# ────────────────────── Bon de Commande ──────────────────────

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("confirmed", "Confirmé"),
        ("in_progress", "En cours"),
        ("delivered", "Livré"),
        ("cancelled", "Annulé"),
    ]
    ref = models.CharField(max_length=64, unique=True, db_index=True)
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders")
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_ice = models.CharField(max_length=15, blank=True)
    customer_address = models.CharField(max_length=500, blank=True)
    customer_po_ref = models.CharField(max_length=64, blank=True, help_text="N° BC du client")

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    payment_terms = models.CharField(max_length=128, default="30 jours")
    notes = models.TextField(blank=True)

    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_purchaseorder"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = _next_ref("BC", PurchaseOrder)
        super().save(*args, **kwargs)


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.20"))
    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_purchaseorderline"

    def save(self, *args, **kwargs):
        self.total_ht = self.qty * self.unit_price
        self.total_vat = self.total_ht * self.vat_rate
        self.total_ttc = self.total_ht + self.total_vat
        super().save(*args, **kwargs)


# ────────────────────── Bon de Livraison ──────────────────────

class DeliveryNote(models.Model):
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("delivered", "Livré"),
        ("partial", "Livraison partielle"),
    ]
    ref = models.CharField(max_length=64, unique=True, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_notes")
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.CharField(max_length=500, blank=True)
    invoice = models.ForeignKey("finance.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_notes")

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_deliverynote"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = _next_ref("BL", DeliveryNote)
        super().save(*args, **kwargs)


class DeliveryNoteLine(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qty_delivered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_deliverynoteline"


# ────────────────────── Bon de Retour ──────────────────────

class ReturnNote(models.Model):
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("approved", "Approuvé"),
        ("rejected", "Rejeté"),
    ]
    ref = models.CharField(max_length=64, unique=True, db_index=True)
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.SET_NULL, null=True, blank=True, related_name="returns")
    invoice = models.ForeignKey("finance.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="returns")
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    reason = models.TextField(blank=True, help_text="Motif du retour")
    return_date = models.DateField(auto_now_add=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_returnnote"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = _next_ref("BRT", ReturnNote)
        super().save(*args, **kwargs)


class ReturnNoteLine(models.Model):
    return_note = models.ForeignKey(ReturnNote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=500, blank=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_returnnoteline"


# ────────────────────── Facture d'Avoir (Credit Note) ──────────────────────

class CreditNote(models.Model):
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("applied", "Appliquée"),
    ]
    ref = models.CharField(max_length=64, unique=True, db_index=True)
    original_invoice = models.ForeignKey(
        "finance.Invoice", on_delete=models.PROTECT, null=True, blank=True, related_name="credit_notes"
    )
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.CharField(max_length=500, blank=True)
    customer_ice = models.CharField(max_length=15, blank=True)
    customer_identifiant_fiscal = models.CharField(max_length=30, blank=True)
    customer_registre_commerce = models.CharField(max_length=30, blank=True)
    customer_taxe_professionnelle = models.CharField(max_length=30, blank=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    reason = models.TextField(blank=True, help_text="Motif de l'avoir")

    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.20"))
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_in_words = models.CharField(max_length=512, blank=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_creditnote"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ref

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = _next_ref("AV", CreditNote)
        super().save(*args, **kwargs)


class CreditNoteLine(models.Model):
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=500, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.20"))
    total_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantAwareManager()

    class Meta:
        db_table = "commerce_creditnoteline"

    def save(self, *args, **kwargs):
        self.total_ht = self.qty * self.unit_price
        self.total_vat = self.total_ht * self.vat_rate
        self.total_ttc = self.total_ht + self.total_vat
        super().save(*args, **kwargs)
