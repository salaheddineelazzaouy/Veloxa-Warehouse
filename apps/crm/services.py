import logging
from django.db import transaction

from .models import Customer
from apps.audit.services import log_access

logger = logging.getLogger(__name__)


def create_customer(tenant, name: str,
                    ice: str = "", identifiant_fiscal: str = "",
                    taxe_professionnelle: str = "", registre_commerce: str = "",
                    phone: str = "", email: str = "", address: str = "",
                    metadata: dict = None, created_by=None) -> Customer:
    customer = Customer.objects.create(
        tenant=tenant, name=name,
        ice=ice, identifiant_fiscal=identifiant_fiscal,
        taxe_professionnelle=taxe_professionnelle,
        registre_commerce=registre_commerce,
        phone=phone, email=email, address=address,
        metadata=metadata or {}
    )
    if created_by:
        log_access(created_by, "create", "crm_customer", customer.id)
    logger.info("Created customer %s", name)
    return customer


def anonymize_customer(customer_id: int, user) -> Customer:
    from apps.tenants.utils import get_current_tenant_id
    with transaction.atomic():
        qs = Customer.objects.select_for_update().filter(pk=customer_id)
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        customer = qs.get()
        customer.name = f"[REDACTED-{customer.id}]"
        customer.phone = ""
        customer.email = ""
        customer.address = ""
        customer.ice = ""
        customer.identifiant_fiscal = ""
        customer.taxe_professionnelle = ""
        customer.registre_commerce = ""
        customer.is_anonymized = True
        customer.save(update_fields=["name", "phone", "email", "address",
                                     "ice", "identifiant_fiscal",
                                     "taxe_professionnelle", "registre_commerce",
                                     "is_anonymized"])
        log_access(user, "update", "crm_customer", customer.id,
                   changes={"anonymized": True})
        logger.info("Anonymized customer %d by %s", customer_id, user)
    return customer
