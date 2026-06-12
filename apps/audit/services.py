import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def log_access(user, action: str, table_name: str, row_id: int = None,
               changes: dict = None, ip_address: str = None, user_agent: str = None):
    AuditLog.objects.create(
        user=user,
        action=action,
        table_name=table_name,
        row_id=row_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent or "",
    )


def get_recent_actions(limit: int = 50):
    return AuditLog.objects.select_related("user").all()[:limit]


def detect_anomaly(minutes: int = 5, threshold: int = 10) -> list:
    from django.utils import timezone
    import datetime
    cutoff = timezone.now() - datetime.timedelta(minutes=minutes)
    recent_pii = AuditLog.objects.filter(
        action="read_pii", timestamp__gte=cutoff
    )
    if recent_pii.count() > threshold:
        logger.warning("Anomaly: %d PII reads in last %d minutes", recent_pii.count(), minutes)
    return list(recent_pii)
