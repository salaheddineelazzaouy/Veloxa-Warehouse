import logging
from datetime import timedelta
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from ..models import StockMovement, Product, StockReservation
from .stock import current_stock
from lib.exceptions import InsufficientStock, InvalidMovement, NotFound

logger = logging.getLogger(__name__)

DEFAULT_RESERVATION_TTL = timedelta(hours=24)


def available_stock(product_id: int) -> int:
    """Physical stock minus all active reservations."""
    total = current_stock(product_id)
    reserved = StockReservation.objects.filter(
        product_id=product_id, status=StockReservation.Status.ACTIVE,
    ).aggregate(total=Sum("qty"))["total"] or 0
    return total - reserved


def reserve_stock(
    product_id: int,
    qty: int,
    order_ref: str,
    user,
    ttl: timedelta | None = None,
) -> StockReservation:
    """Atomically reserve stock for a pending order.

    Locks both the Product row and checks available stock inside a
    transaction to prevent two concurrent reservations from exceeding
    available inventory.
    """
    if qty <= 0:
        raise InvalidMovement("Reservation quantity must be positive")

    if ttl is None:
        ttl = DEFAULT_RESERVATION_TTL

    with transaction.atomic():
        product = Product.objects.select_for_update().get(
            pk=product_id, is_active=True,
        )

        avail = available_stock(product_id)
        if qty > avail:
            raise InsufficientStock(
                f"Cannot reserve {qty} of {product.sku}: only {avail} available"
            )

        reservation = StockReservation.objects.create(
            product=product,
            qty=qty,
            order_ref=order_ref,
            status=StockReservation.Status.ACTIVE,
            expires_at=timezone.now() + ttl,
            created_by=user,
            tenant=user.tenant,
        )

        logger.info(
            "Reservation created product=%s qty=%d ref=%s user=%s expires=%s",
            product.sku, qty, order_ref, user, reservation.expires_at,
        )

    return reservation


def confirm_reservation(reservation_id: int, user) -> dict:
    """Confirm a reservation — creates the outbound StockMovement.

    This is the only path that should create outbound movements for
    reserved stock. Returns the movement and updated stock.
    """
    with transaction.atomic():
        reservation = StockReservation.objects.select_for_update().get(
            pk=reservation_id,
        )

        if reservation.status != StockReservation.Status.ACTIVE:
            raise InvalidMovement(
                f"Reservation {reservation_id} is {reservation.status}, cannot confirm"
            )

        if reservation.is_expired:
            reservation.status = StockReservation.Status.EXPIRED
            reservation.save(update_fields=["status"])
            raise InvalidMovement(f"Reservation {reservation_id} has expired")

        product = Product.objects.select_for_update().get(
            pk=reservation.product_id,
        )

        movement = StockMovement.objects.create(
            product=product,
            qty=-reservation.qty,
            type=StockMovement.Type.OUTBOUND,
            reference=reservation.order_ref,
            note=f"Reserved stock confirmed (RES-{reservation.id})",
            created_by=user,
            tenant=user.tenant,
        )

        reservation.status = StockReservation.Status.FULFILLED
        reservation.save(update_fields=["status"])

        stock_after = current_stock(reservation.product_id)

        logger.info(
            "Reservation confirmed res=%d product=%s qty=%d ref=%s user=%s",
            reservation.id, product.sku, reservation.qty, reservation.order_ref, user,
        )

    return {"movement": movement, "stock_after": stock_after}


def release_reservation(reservation_id: int, user, reason: str = "") -> StockReservation:
    """Release a reservation — returns stock to available pool."""
    with transaction.atomic():
        reservation = StockReservation.objects.select_for_update().get(
            pk=reservation_id,
        )

        if reservation.status != StockReservation.Status.ACTIVE:
            raise InvalidMovement(
                f"Reservation {reservation_id} is {reservation.status}, cannot release"
            )

        reservation.status = StockReservation.Status.RELEASED
        reservation.save(update_fields=["status"])

        logger.info(
            "Reservation released res=%d product=%s qty=%d ref=%s reason=%s user=%s",
            reservation.id, reservation.product_id, reservation.qty,
            reservation.order_ref, reason, user,
        )

    return reservation


def expire_stale_reservations() -> list[int]:
    """Expire all active reservations past their TTL. Returns list of IDs."""
    with transaction.atomic():
        stale = StockReservation.objects.select_for_update().filter(
            status=StockReservation.Status.ACTIVE,
            expires_at__lt=timezone.now(),
        )
        ids = list(stale.values_list("id", flat=True))
        stale.update(status=StockReservation.Status.EXPIRED)

        if ids:
            logger.info("Expired %d stale reservations: %s", len(ids), ids)

    return ids
