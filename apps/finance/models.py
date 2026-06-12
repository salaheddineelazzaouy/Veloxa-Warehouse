from django.db import models
from django.contrib.auth import get_user_model


class Invoice(models.Model):
    invoice_ref = models.CharField(max_length=64, unique=True, db_index=True)
    order_ref = models.CharField(max_length=64, db_index=True)
    customer = models.ForeignKey(
        "crm.Customer", on_delete=models.PROTECT, null=True, blank=True
    )
    total = models.DecimalField(max_digits=14, decimal_places=2)
    source = models.CharField(max_length=16, default="pos")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_invoice"

    def __str__(self):
        return self.invoice_ref


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("warehouse.Product", on_delete=models.PROTECT)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "finance_invoiceline"

    def __str__(self):
        return f"{self.invoice.invoice_ref} - {self.product.sku}"
