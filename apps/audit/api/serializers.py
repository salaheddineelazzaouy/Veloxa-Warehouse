from rest_framework import serializers
from ..models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = ("id", "timestamp", "user_id", "user_username", "action",
                  "table_name", "row_id", "changes", "ip_address")
        read_only_fields = fields
