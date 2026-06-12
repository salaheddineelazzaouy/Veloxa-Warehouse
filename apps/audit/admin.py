from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "table_name", "row_id", "ip_address")
    list_filter = ("action", "table_name")
    readonly_fields = ("timestamp", "user", "action", "table_name", "row_id", "changes", "ip_address")
