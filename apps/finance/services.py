import logging
from decimal import Decimal
from django.db import transaction

from .models import Invoice, InvoiceLine

logger = logging.getLogger(__name__)


def create_invoice(order_ref: str, lines: list[dict], user,
                   customer_id: int = None, tenant=None) -> Invoice:
    with transaction.atomic():
        total = sum(Decimal(str(line["qty"])) * Decimal(str(line["unit_price"]))
                    for line in lines)
        ice = if_ = tp = rc = ""
        if customer_id:
            from apps.crm.models import Customer
            try:
                c = Customer.objects.get(id=customer_id)
                ice = c.ice or ""
                if_ = c.identifiant_fiscal or ""
                tp = c.taxe_professionnelle or ""
                rc = c.registre_commerce or ""
            except Customer.DoesNotExist:
                pass
        invoice = Invoice.objects.create(
            invoice_ref=f"INV-{order_ref}",
            order_ref=order_ref,
            customer_id=customer_id,
            customer_ice=ice,
            customer_identifiant_fiscal=if_,
            customer_taxe_professionnelle=tp,
            customer_registre_commerce=rc,
            total=total,
            created_by=user,
            tenant=tenant,
        )
        for line in lines:
            InvoiceLine.objects.create(
                invoice=invoice,
                product_id=line["product_id"],
                qty=line["qty"],
                unit_price=line["unit_price"],
                total=Decimal(str(line["qty"])) * Decimal(str(line["unit_price"])),
                tenant=tenant,
            )
        logger.info("Invoice %s created with %d lines", invoice.invoice_ref, len(lines))
    return invoice


def update_invoice(invoice_id: int, order_ref: str = None,
                   customer_id: int = None, source: str = None,
                   lines: list[dict] = None, user=None) -> Invoice:
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)
        if order_ref is not None:
            invoice.order_ref = order_ref
        if customer_id is not None:
            invoice.customer_id = customer_id
            try:
                from apps.crm.models import Customer
                c = Customer.objects.get(id=customer_id)
                invoice.customer_ice = c.ice or ""
                invoice.customer_identifiant_fiscal = c.identifiant_fiscal or ""
                invoice.customer_taxe_professionnelle = c.taxe_professionnelle or ""
                invoice.customer_registre_commerce = c.registre_commerce or ""
            except Customer.DoesNotExist:
                pass
        if source is not None:
            invoice.source = source
        if lines is not None:
            invoice.lines.all().delete()
            total = Decimal("0")
            for line in lines:
                line_total = Decimal(str(line["qty"])) * Decimal(str(line["unit_price"]))
                InvoiceLine.objects.create(
                    invoice=invoice,
                    product_id=line["product_id"],
                    qty=line["qty"],
                    unit_price=line["unit_price"],
                    total=line_total,
                    tenant=invoice.tenant,
                )
                total += line_total
            invoice.total = total
        invoice.save()
        logger.info("Invoice %s updated by %s", invoice.invoice_ref, user)
    return invoice


def delete_invoice(invoice_id: int, user) -> None:
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)
        ref = invoice.invoice_ref
        invoice.delete()
        logger.info("Invoice %s deleted by %s", ref, user)


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
