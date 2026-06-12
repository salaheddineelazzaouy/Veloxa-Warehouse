import logging
from django.db import transaction

from .models import Customer
from apps.audit.services import log_access

logger = logging.getLogger(__name__)


def create_customer(name: str, phone: str = "", email: str = "",
                    address: str = "", created_by=None) -> Customer:
    customer = Customer.objects.create(
        name=name, phone=phone, email=email, address=address
    )
    if created_by:
        log_access(created_by, "create", "crm_customer", customer.id)
    logger.info("Created customer %s", name)
    return customer


def anonymize_customer(customer_id: int, user) -> Customer:
    with transaction.atomic():
        customer = Customer.objects.select_for_update().get(pk=customer_id)
        customer.name = f"[REDACTED-{customer.id}]"
        customer.phone = ""
        customer.email = ""
        customer.address = ""
        customer.is_anonymized = True
        customer.save(update_fields=["name", "phone", "email", "address", "is_anonymized"])
        log_access(user, "update", "crm_customer", customer.id,
                   changes={"anonymized": True})
        logger.info("Anonymized customer %d by %s", customer_id, user)
    return customer
