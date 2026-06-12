import logging
from decimal import Decimal
from django.db import transaction

from .models import Invoice, InvoiceLine
from apps.warehouse.services.stock import current_stock

logger = logging.getLogger(__name__)


def create_invoice(order_ref: str, lines: list[dict], user,
                   customer_id: int = None) -> Invoice:
    with transaction.atomic():
        total = sum(Decimal(str(l["qty"])) * Decimal(str(l["unit_price"]))
                    for l in lines)
        invoice = Invoice.objects.create(
            invoice_ref=f"INV-{order_ref}",
            order_ref=order_ref,
            customer_id=customer_id,
            total=total,
            created_by=user,
        )
        for line in lines:
            InvoiceLine.objects.create(
                invoice=invoice,
                product_id=line["product_id"],
                qty=line["qty"],
                unit_price=line["unit_price"],
                total=Decimal(str(line["qty"])) * Decimal(str(line["unit_price"])),
            )
        logger.info("Invoice %s created with %d lines", invoice.invoice_ref, len(lines))
    return invoice


def calculate_cogs(product_id: int) -> Decimal:
    movements = InvoiceLine.objects.filter(
        product_id=product_id
    ).select_related("invoice")
    total_qty = 0
    total_cost = Decimal("0")
    for line in movements:
        total_qty += line.qty
        total_cost += line.total
    if total_qty == 0:
        return Decimal("0")
    return total_cost / Decimal(str(total_qty))
