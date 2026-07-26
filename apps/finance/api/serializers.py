from rest_framework import serializers
from ..models import Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True, default=None)
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)

    class Meta:
        model = InvoiceLine
        fields = ("id", "product_id", "product_sku", "product_name",
                  "description", "qty", "unit_price", "vat_rate",
                  "total_ht", "total_vat", "total_ttc", "total")
        read_only_fields = ("id", "total_ht", "total_vat", "total_ttc", "total")


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(read_only=True, default="")
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Invoice
        fields = (
            "id", "invoice_ref", "order_ref",
            "customer_id", "customer_name",
            "customer_address", "customer_ice",
            "customer_identifiant_fiscal", "customer_taxe_professionnelle",
            "customer_registre_commerce",
            "total_ht", "vat_rate", "total_vat", "total_ttc", "total",
            "amount_in_words", "vat_exempt_notice",
            "payment_terms", "payment_due_date",
            "source", "created_by", "created_by_username",
            "created_at", "lines",
        )
        read_only_fields = fields


class InvoiceCreateSerializer(serializers.Serializer):
    order_ref = serializers.CharField(max_length=64)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    lines = serializers.ListField(min_length=1)
    vat_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0.20)
    payment_terms = serializers.CharField(max_length=128, required=False, default="30 jours")
    payment_due_date = serializers.DateField(required=False, allow_null=True)

    def validate_lines(self, value):
        for i, line in enumerate(value):
            if not all(k in line for k in ("product_id", "qty", "unit_price")):
                raise serializers.ValidationError(
                    f"Line {i}: missing product_id, qty, or unit_price"
                )
        return value
