from django.db import models
from django.contrib.auth import get_user_model


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"
        READ_PII = "read_pii"

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=16, choices=Action.choices)
    table_name = models.CharField(max_length=64)
    row_id = models.IntegerField(null=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-timestamp"]
        permissions = [
            ("run_reconciliation", "Can run reconciliation"),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.action} on {self.table_name} by {self.user}"
