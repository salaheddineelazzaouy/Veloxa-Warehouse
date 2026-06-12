from rest_framework import serializers
from ..models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "phone", "email", "address",
                  "is_anonymized", "created_at", "updated_at")
        read_only_fields = ("id", "is_anonymized", "created_at", "updated_at")


class CustomerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("name", "phone", "email", "address")
