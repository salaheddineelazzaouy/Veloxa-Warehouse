import re
from rest_framework import serializers
from ..models import Product, StockMovement, StockReservation


class ProductSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    reserved = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    unit_name = serializers.CharField(source="unit.abbreviation", read_only=True, default=None)

    class Meta:
        model = Product
        fields = ("id", "sku", "name", "description", "category", "category_name",
                  "unit", "unit_name", "cost_price",
                  "is_active", "stock", "available", "reserved", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_stock(self, obj) -> int:
        from ..services.stock import current_stock
        return current_stock(obj.id)

    def get_available(self, obj) -> int:
        from ..services.reservation import available_stock
        return available_stock(obj.id)

    def get_reserved(self, obj) -> int:
        from ..models import StockReservation
        from django.db.models import Sum
        return StockReservation.objects.filter(
            product_id=obj.id, status=StockReservation.Status.ACTIVE,
        ).aggregate(total=Sum("qty"))["total"] or 0


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "sku", "name", "description", "category", "unit",
                  "cost_price", "is_active")
        read_only_fields = ("id",)

    def validate_sku(self, value):
        if not re.match(r"^[A-Za-z0-9\-_]+$", value):
            raise serializers.ValidationError("SKU must be alphanumeric with hyphens/underscores only")
        return value


class InboundSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=100_000)
    po_ref = serializers.CharField(max_length=64)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
    location_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_po_ref(self, value):
        if not re.match(r"^[A-Za-z0-9\-]+$", value):
            raise serializers.ValidationError("PO reference must be alphanumeric")
        return value


class OutboundSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=100_000)
    so_ref = serializers.CharField(max_length=64)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
    location_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_so_ref(self, value):
        if not re.match(r"^[A-Za-z0-9\-]+$", value):
            raise serializers.ValidationError("SO reference must be alphanumeric")
        return value


class AdjustmentSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField()
    reason = serializers.CharField(max_length=500)

    def validate_qty(self, value):
        if value == 0:
            raise serializers.ValidationError("Adjustment quantity cannot be zero")
        return value


class ReconcileSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    physical_count = serializers.IntegerField(min_value=0)


class MovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = ("id", "product_id", "product_sku", "product_name", "qty",
                  "type", "reference", "note", "location_id", "created_by_id",
                  "created_by_username", "created_at")
        read_only_fields = fields


class ReserveSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=100_000)
    order_ref = serializers.CharField(max_length=64)
    ttl_hours = serializers.IntegerField(min_value=1, max_value=720, required=False, default=24)

    def validate_order_ref(self, value):
        if not re.match(r"^[A-Za-z0-9\-_]+$", value):
            raise serializers.ValidationError("Order reference must be alphanumeric")
        return value


class ReservationSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = StockReservation
        fields = ("id", "product_id", "product_sku", "product_name", "qty",
                  "order_ref", "status", "expires_at", "created_by_id",
                  "created_by_username", "created_at", "updated_at")
        read_only_fields = fields
