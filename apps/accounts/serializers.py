from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from apps.subscriptions.models import SubscriptionPlan

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default="viewer")
    plan_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "plan_id")

    def validate_plan_id(self, value):
        if value is None:
            return value
        if not SubscriptionPlan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive plan.")
        return value

    def create(self, validated_data):
        from .services import create_user
        plan_id = validated_data.pop("plan_id", None)
        user = create_user(**validated_data)
        if plan_id:
            from apps.subscriptions.models import Subscription
            Subscription.objects.create(
                user=user,
                plan_id=plan_id,
                status="pending_payment",
                billing_cycle="monthly",
                tenant=user.tenant,
            )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "role", "is_active", "date_joined")
