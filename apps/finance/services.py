import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Max

from .models import Invoice, InvoiceLine
from .number_to_french import number_to_french

logger = logging.getLogger(__name__)

VAT_RATE_MAP = {
    "20": Decimal("0.20"),
    "14": Decimal("0.14"),
    "10": Decimal("0.10"),
    "7": Decimal("0.07"),
    "0": Decimal("0.00"),
}


def _next_invoice_ref(tenant, year=None):
    from django.utils import timezone
    if year is None:
        year = timezone.now().year
    prefix = f"FAC-{year}-"
    last = (
        Invoice.objects.filter(invoice_ref__startswith=prefix)
        .aggregate(max_ref=Max("invoice_ref"))["max_ref"]
    )
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def _resolve_vat_rate(value):
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        return VAT_RATE_MAP.get(value.strip().replace("%", ""), Decimal("0.20"))
    return Decimal("0.20")


def _gather_customer_info(customer_id):
    ice = if_ = tp = rc = name = address = ""
    if customer_id:
        from apps.crm.models import Customer
        try:
            c = Customer.objects.get(id=customer_id)
            name = c.name or ""
            address = c.address or ""
            ice = c.ice or ""
            if_ = c.identifiant_fiscal or ""
            tp = c.taxe_professionnelle or ""
            rc = c.registre_commerce or ""
        except Customer.DoesNotExist:
            pass
    return {
        "customer_name": name,
        "customer_address": address,
        "customer_ice": ice,
        "customer_identifiant_fiscal": if_,
        "customer_taxe_professionnelle": tp,
        "customer_registre_commerce": rc,
    }


def _vat_exempt_notice(tenant):
    if not tenant:
        return ""
    regime = getattr(tenant, "tax_regime", "standard")
    if regime == "auto_entrepreneur":
        return "TVA non applicable - Article 91-II-3\u00b0 du Code G\u00e9n\u00e9ral des Imp\u00f4ts"
    if regime == "export":
        return "Exon\u00e9r\u00e9 de TVA en vertu de l\u2019Article 92 du Code G\u00e9n\u00e9ral des Imp\u00f4ts"
    return ""


@transaction.atomic
def create_invoice(order_ref: str, lines: list[dict], user,
                   customer_id: int = None, tenant=None,
                   vat_rate=None, payment_terms="30 jours",
                   payment_due_date=None) -> Invoice:

    inv_vat = _resolve_vat_rate(vat_rate) if vat_rate is not None else Decimal("0.20")
    if tenant and getattr(tenant, "tax_regime", "standard") in ("auto_entrepreneur", "export"):
        inv_vat = Decimal("0.00")

    cust_info = _gather_customer_info(customer_id)
    invoice_ref = _next_invoice_ref(tenant)

    invoice = Invoice.objects.create(
        invoice_ref=invoice_ref,
        order_ref=order_ref,
        customer_id=customer_id,
        **cust_info,
        vat_rate=inv_vat,
        payment_terms=payment_terms,
        payment_due_date=payment_due_date,
        vat_exempt_notice=_vat_exempt_notice(tenant),
        created_by=user,
        tenant=tenant,
    )

    total_ht = Decimal("0")
    total_vat = Decimal("0")

    for line in lines:
        qty = Decimal(str(line["qty"]))
        price = Decimal(str(line["unit_price"]))
        line_vat = _resolve_vat_rate(line.get("vat_rate", inv_vat))
        if tenant and getattr(tenant, "tax_regime", "standard") in ("auto_entrepreneur", "export"):
            line_vat = Decimal("0.00")

        line_ht = qty * price
        line_vat_amt = line_ht * line_vat
        line_ttc = line_ht + line_vat_amt
        desc = line.get("description", "")

        InvoiceLine.objects.create(
            invoice=invoice,
            product_id=line["product_id"],
            description=desc,
            qty=qty,
            unit_price=price,
            vat_rate=line_vat,
            total_ht=line_ht,
            total_vat=line_vat_amt,
            total_ttc=line_ttc,
            total=line_ttc,
            tenant=tenant,
        )
        total_ht += line_ht
        total_vat += line_vat_amt

    total_ttc = total_ht + total_vat
    invoice.total_ht = total_ht
    invoice.total_vat = total_vat
    invoice.total_ttc = total_ttc
    invoice.total = total_ttc
    invoice.amount_in_words = number_to_french(total_ttc)
    invoice.save()

    logger.info("Invoice %s created (%s HT, %s TVA, %s TTC)",
                invoice.invoice_ref, total_ht, total_vat, total_ttc)
    return invoice


@transaction.atomic
def update_invoice(invoice_id: int, order_ref: str = None,
                   customer_id: int = None, source: str = None,
                   lines: list[dict] = None, user=None,
                   vat_rate=None, payment_terms=None,
                   payment_due_date=None) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(id=invoice_id)

    if order_ref is not None:
        invoice.order_ref = order_ref
    if source is not None:
        invoice.source = source
    if payment_terms is not None:
        invoice.payment_terms = payment_terms
    if payment_due_date is not None:
        invoice.payment_due_date = payment_due_date

    if customer_id is not None:
        invoice.customer_id = customer_id
        cust_info = _gather_customer_info(customer_id)
        for k, v in cust_info.items():
            setattr(invoice, k, v)

    if vat_rate is not None:
        invoice.vat_rate = _resolve_vat_rate(vat_rate)
        if invoice.tenant and getattr(invoice.tenant, "tax_regime", "standard") in ("auto_entrepreneur", "export"):
            invoice.vat_rate = Decimal("0.00")

    if lines is not None:
        invoice.lines.all().delete()
        inv_vat = invoice.vat_rate
        total_ht = Decimal("0")
        total_vat = Decimal("0")
        for line in lines:
            qty = Decimal(str(line["qty"]))
            price = Decimal(str(line["unit_price"]))
            line_vat = _resolve_vat_rate(line.get("vat_rate", inv_vat))
            line_ht = qty * price
            line_vat_amt = line_ht * line_vat
            line_ttc = line_ht + line_vat_amt

            InvoiceLine.objects.create(
                invoice=invoice,
                product_id=line["product_id"],
                description=line.get("description", ""),
                qty=qty,
                unit_price=price,
                vat_rate=line_vat,
                total_ht=line_ht,
                total_vat=line_vat_amt,
                total_ttc=line_ttc,
                total=line_ttc,
                tenant=invoice.tenant,
            )
            total_ht += line_ht
            total_vat += line_vat_amt

        invoice.total_ht = total_ht
        invoice.total_vat = total_vat
        invoice.total_ttc = total_ht + total_vat
        invoice.total = invoice.total_ttc

    invoice.amount_in_words = number_to_french(invoice.total_ttc)
    invoice.vat_exempt_notice = _vat_exempt_notice(invoice.tenant)
    invoice.save()
    logger.info("Invoice %s updated by %s", invoice.invoice_ref, user)
    return invoice


@transaction.atomic
def delete_invoice(invoice_id: int, user) -> None:
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
