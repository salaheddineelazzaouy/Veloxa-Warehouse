from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentTransaction


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "name", "description", "price_monthly", "price_yearly",
            "price_display", "is_active", "features",
        ]
        read_only_fields = ["id"]

    def get_price_display(self, obj):
        if obj.price_monthly == 0:
            return "Custom"
        return f"MAD {obj.price_monthly:,.2f}/mo"


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "user", "plan", "plan_id", "status", "start_date",
            "end_date", "billing_cycle", "last_payment_date",
            "next_payment_date", "created_at",
        ]
        read_only_fields = [
            "id", "user", "status", "start_date", "end_date",
            "last_payment_date", "next_payment_date", "created_at",
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    subscription_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = PaymentTransaction
        fields = [
            "id", "user", "subscription", "subscription_id", "amount",
            "currency", "payment_method", "reference_number", "proof_image",
            "status", "verified_by", "verified_at", "notes", "plan",
            "billing_cycle", "created_at",
        ]
        read_only_fields = [
            "id", "user", "subscription", "status", "verified_by",
            "verified_at", "created_at",
        ]


class PaymentRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(
        choices=["monthly", "yearly"]
    )
    reference_number = serializers.CharField(max_length=100)
    proof_image = serializers.ImageField()
    notes = serializers.CharField(required=False, allow_blank=True)
