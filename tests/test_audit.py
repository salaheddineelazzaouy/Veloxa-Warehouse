"""Tests for audit logging — PII-safe, immutable audit trail."""
import pytest
from apps.audit.models import AuditLog
from apps.audit.services import log_access


class TestAuditLog:
    def test_log_creation(self, admin_user):
        log_access(admin_user, "create", "warehouse_product", row_id=1,
                   changes={"sku": "TEST"})
        assert AuditLog.objects.count() == 1
        entry = AuditLog.objects.first()
        assert entry.action == "create"
        assert entry.table_name == "warehouse_product"
        assert entry.user == admin_user

    def test_multiple_logs(self, admin_user):
        for i in range(3):
            log_access(admin_user, "read_pii", "crm_customer", row_id=i,
                       changes={"action": "view"})
        assert AuditLog.objects.count() == 3

    def test_log_without_user(self, db):
        log_access(None, "read_pii", "crm_customer", row_id=1)
        entry = AuditLog.objects.first()
        assert entry.user is None
