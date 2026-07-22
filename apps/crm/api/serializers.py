from rest_framework import serializers
from ..models import Customer


def validate_ice(value):
    if value and not value.isdigit():
        raise serializers.ValidationError("ICE must contain only digits.")
    if value and len(value) != 15:
        raise serializers.ValidationError("ICE must be exactly 15 digits.")
    return value


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "ice", "identifiant_fiscal",
                  "taxe_professionnelle", "registre_commerce",
                  "phone", "email", "address",
                  "is_active", "is_anonymized", "metadata",
                  "created_at", "updated_at")
        read_only_fields = ("id", "is_anonymized", "created_at", "updated_at")

    def validate_ice(self, value):
        return validate_ice(value)


class CustomerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("name", "ice", "identifiant_fiscal",
                  "taxe_professionnelle", "registre_commerce",
                  "phone", "email", "address",
                  "is_active", "metadata")

    def validate_ice(self, value):
        return validate_ice(value)
