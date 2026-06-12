import logging
from django.db import transaction
from django.db.models import Q

from ..models import StockMovement, Product
from .stock import current_stock
from lib.exceptions import InsufficientStock, DuplicateReference, InvalidMovement

logger = logging.getLogger(__name__)


def fulfill_sales_order(
    product_id: int,
    qty: int,
    so_ref: str,
    user,
    note: str = "",
    location_id: int | None = None,
) -> dict:
    if qty <= 0:
        raise InvalidMovement("Quantity must be positive for outbound")

    with transaction.atomic():
        product = Product.objects.select_for_update().get(
            pk=product_id, is_active=True
        )

        exists = StockMovement.objects.filter(
            Q(reference=so_ref) & Q(type="outbound")
        ).exists()
        if exists:
            raise DuplicateReference(f"SO {so_ref} already fulfilled")

        available = current_stock(product_id)
        if qty > available:
            raise InsufficientStock(
                f"Requested {qty}, available {available}"
            )

        movement = StockMovement.objects.create(
            product=product,
            qty=-qty,
            type=StockMovement.Type.OUTBOUND,
            reference=so_ref,
            note=note,
            location_id=location_id,
            created_by=user,
        )

        stock_after = current_stock(product_id)

        logger.info(
            "Outbound product=%s qty=%+d ref=%s user=%s stock_after=%d",
            product.sku, -qty, so_ref, user, stock_after,
        )

    return {
        "movement": movement,
        "stock_after": stock_after,
    }
