from rest_framework import serializers
from ..models import BackOrder


class BackOrderSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    qty_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = BackOrder
        fields = ("id", "product_id", "product_sku", "product_name", "qty",
                  "qty_fulfilled", "qty_remaining", "status", "sales_order_ref",
                  "created_by", "created_at", "updated_at")
        read_only_fields = fields



class BackOrderCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1)
    sales_order_ref = serializers.CharField(max_length=64, required=False, allow_blank=True)


class FulfillSerializer(serializers.Serializer):
    qty = serializers.IntegerField(min_value=1)
