from rest_framework import serializers
from ..models import Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ("id", "product_id", "qty", "unit_price", "total")
        read_only_fields = ("id", "total")


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = ("id", "invoice_ref", "order_ref", "customer_id", "total",
                  "source", "created_by", "created_at", "lines")
        read_only_fields = fields


class InvoiceCreateSerializer(serializers.Serializer):
    order_ref = serializers.CharField(max_length=64)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    lines = serializers.ListField(min_length=1)

    def validate_lines(self, value):
        for i, line in enumerate(value):
            if not all(k in line for k in ("product_id", "qty", "unit_price")):
                raise serializers.ValidationError(
                    f"Line {i}: missing product_id, qty, or unit_price"
                )
        return value
