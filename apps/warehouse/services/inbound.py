import logging
from django.db import transaction
from django.db.models import Q

from ..models import StockMovement, Product
from lib.exceptions import DuplicateReference, InvalidMovement

logger = logging.getLogger(__name__)


def receive_purchase_order(
    product_id: int,
    qty: int,
    po_ref: str,
    user,
    note: str = "",
    location_id: int | None = None,
) -> StockMovement:
    if qty <= 0:
        raise InvalidMovement("Quantity must be positive for inbound")

    with transaction.atomic():
        product = Product.objects.select_for_update().get(
            pk=product_id, is_active=True
        )

        exists = StockMovement.objects.filter(
            Q(reference=po_ref) & Q(type="inbound")
        ).exists()
        if exists:
            raise DuplicateReference(f"PO {po_ref} already received")

        movement = StockMovement.objects.create(
            product=product,
            qty=+qty,
            type=StockMovement.Type.INBOUND,
            reference=po_ref,
            note=note,
            location_id=location_id,
            created_by=user,
            tenant=user.tenant,
        )

        logger.info(
            "Inbound product=%s qty=%+d ref=%s user=%s",
            product.sku, qty, po_ref, user,
        )

    return movement
