from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError

from config.decorators import role_required, WRITE_ROLES
from apps.tenants.utils import bypass_tenant
from apps.crm.models import Customer
from apps.warehouse.models import Product

from .models import (
    Quote, QuoteLine, PurchaseOrder, PurchaseOrderLine,
    DeliveryNote, DeliveryNoteLine, ReturnNote, ReturnNoteLine,
    CreditNote, CreditNoteLine,
)


def _gather_customer(customer_id):
    ice = if_ = tp = rc = name = address = ""
    if customer_id:
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
        "customer_name": name, "customer_address": address,
        "customer_ice": ice, "customer_identifiant_fiscal": if_,
        "customer_registre_commerce": rc, "customer_taxe_professionnelle": tp,
    }


def _get_tenant_object_or_404(model, pk, user):
    if user.is_superuser:
        return get_object_or_404(model, pk=pk)
    return get_object_or_404(model, pk=pk, tenant=user.tenant)


def _get_vat_rate(tenant, override=None):
    if tenant and getattr(tenant, "tax_regime", "standard") in ("auto_entrepreneur", "export"):
        return Decimal("0.00")
    if override is not None:
        return Decimal(str(override))
    return Decimal("0.20")


def _calc_lines(lines_data, default_vat):
    total_ht = Decimal("0")
    total_vat = Decimal("0")
    for line in lines_data:
        line["vat_rate"] = Decimal(str(line.get("vat_rate", default_vat)))
        line["total_ht"] = line["qty"] * line["unit_price"]
        line["total_vat"] = line["total_ht"] * line["vat_rate"]
        line["total_ttc"] = line["total_ht"] + line["total_vat"]
        total_ht += line["total_ht"]
        total_vat += line["total_vat"]
    return total_ht, total_vat


def _parse_lines(request):
    product_ids = request.POST.getlist("line_product[]")
    qtys = request.POST.getlist("line_qty[]")
    prices = request.POST.getlist("line_price[]")
    vat_rates = request.POST.getlist("line_vat[]")
    descs = request.POST.getlist("line_description[]")
    lines = []
    for i, (pid, qty, price) in enumerate(zip(product_ids, qtys, prices)):
        if pid and qty and price:
            vr = vat_rates[i] if i < len(vat_rates) else "20"
            desc = descs[i] if i < len(descs) else ""
            lines.append({
                "product_id": int(pid),
                "qty": Decimal(str(qty)),
                "unit_price": Decimal(str(price)),
                "vat_rate": Decimal(str(vr)) if vr else Decimal("20"),
                "description": desc,
            })
    return lines


def _parse_bl_lines(request):
    product_ids = request.POST.getlist("line_product[]")
    qtys_ordered = request.POST.getlist("line_qty_ordered[]")
    qtys_delivered = request.POST.getlist("line_qty_delivered[]")
    descs = request.POST.getlist("line_description[]")
    lines = []
    for i, (pid, qo, qd) in enumerate(zip(product_ids, qtys_ordered, qtys_delivered)):
        if pid:
            desc = descs[i] if i < len(descs) else ""
            lines.append({
                "product_id": int(pid),
                "qty_ordered": Decimal(str(qo)) if qo else Decimal("0"),
                "qty_delivered": Decimal(str(qd)) if qd else Decimal("0"),
                "description": desc,
            })
    return lines


def _po_delivered_quantities(po):
    delivered = (
        DeliveryNoteLine.objects
        .filter(delivery_note__purchase_order=po)
        .values("product_id")
        .annotate(total_delivered=Sum("qty_delivered"))
    )
    return {str(item["product_id"]): item["total_delivered"] for item in delivered}


# ════════════════════════ QUOTES (DEVIS) ════════════════════════

@login_required
def quote_list(request):
    qs = Quote.objects.select_related("customer", "created_by").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(ref__icontains=q) | Q(customer_name__icontains=q) | Q(customer__name__icontains=q))
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    return render(request, "commerce/quote_list.html", {"quotes": qs, "q": q, "status_filter": status})


@login_required
def quote_detail(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    lines = quote.lines.select_related("product").all()
    return render(request, "commerce/quote_detail.html", {"quote": quote, "lines": lines, "tenant": request.user.tenant})


@login_required
@role_required(*WRITE_ROLES)
def quote_create(request):
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    default_vat = _get_vat_rate(tenant)
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        validity_days = int(request.POST.get("validity_days", 30))
        payment_terms = request.POST.get("payment_terms", "30 jours")
        notes = request.POST.get("notes", "")
        default_vat = Decimal(request.POST.get("default_vat_rate", "20")) / 100
        default_vat = _get_vat_rate(tenant, default_vat)
        lines_data = _parse_lines(request)
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            total_ht, total_vat = _calc_lines(lines_data, default_vat)
            total_ttc = total_ht + total_vat
            from apps.finance.number_to_french import number_to_french
            cust = _gather_customer(customer_id)
            quote = Quote.objects.create(
                customer_id=customer_id, **cust,
                status="draft", validity_days=validity_days,
                payment_terms=payment_terms, notes=notes,
                total_ht=total_ht, vat_rate=default_vat,
                total_vat=total_vat, total_ttc=total_ttc,
                amount_in_words=number_to_french(total_ttc),
                created_by=request.user, tenant=tenant,
            )
            for ld in lines_data:
                QuoteLine.objects.create(quote=quote, tenant=tenant, **ld)
            messages.success(request, f"Devis {quote.ref} créé.")
            return redirect("quote-detail", pk=quote.pk)
    return render(request, "commerce/quote_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": False, "default_vat": default_vat,
    })


@login_required
@role_required(*WRITE_ROLES)
def quote_edit(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    existing_lines = quote.lines.select_related("product").all()
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        quote.status = request.POST.get("status", quote.status)
        quote.validity_days = int(request.POST.get("validity_days", quote.validity_days))
        quote.payment_terms = request.POST.get("payment_terms", quote.payment_terms)
        quote.notes = request.POST.get("notes", "")
        default_vat = Decimal(request.POST.get("default_vat_rate", "20")) / 100
        default_vat = _get_vat_rate(tenant, default_vat)
        quote.vat_rate = default_vat
        customer_id_new = customer_id if customer_id else quote.customer_id
        cust = _gather_customer(customer_id_new)
        for k, v in cust.items():
            setattr(quote, k, v)
        quote.customer_id = customer_id_new
        lines_data = _parse_lines(request)
        if lines_data:
            quote.lines.all().delete()
            total_ht, total_vat = _calc_lines(lines_data, default_vat)
            quote.total_ht = total_ht
            quote.total_vat = total_vat
            quote.total_ttc = total_ht + total_vat
            from apps.finance.number_to_french import number_to_french
            quote.amount_in_words = number_to_french(quote.total_ttc)
            for ld in lines_data:
                QuoteLine.objects.create(quote=quote, tenant=tenant, **ld)
        quote.save()
        messages.success(request, f"Devis {quote.ref} mis à jour.")
        return redirect("quote-detail", pk=quote.pk)
    return render(request, "commerce/quote_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": True, "quote": quote, "existing_lines": existing_lines,
        "default_vat": quote.vat_rate,
    })


@login_required
@role_required(*WRITE_ROLES)
def quote_delete(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    if request.method == "POST":
        ref = quote.ref
        quote.delete()
        messages.success(request, f"Devis {ref} supprimé.")
        return redirect("quote-list")
    return render(request, "commerce/confirm_delete.html", {"object": quote, "label": f"Devis {quote.ref}"})


@login_required
@role_required(*WRITE_ROLES)
def quote_accept(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    quote.status = "accepted"
    quote.save()
    messages.success(request, f"Devis {quote.ref} accepté. Vous pouvez créer un Bon de Commande.")
    return redirect("quote-detail", pk=quote.pk)


@login_required
@role_required(*WRITE_ROLES)
def quote_reject(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    quote.status = "rejected"
    quote.save()
    messages.warning(request, f"Devis {quote.ref} refusé.")
    return redirect("quote-detail", pk=quote.pk)


@login_required
@role_required(*WRITE_ROLES)
def quote_convert_to_po(request, pk):
    quote = _get_tenant_object_or_404(Quote, pk, request.user)
    if quote.status != "accepted":
        messages.error(request, "Seuls les devis acceptés peuvent être convertis en BC.")
        return redirect("quote-detail", pk=quote.pk)

    tenant = request.user.tenant
    quote_lines = quote.lines.select_related("product").all()

    total_ht = quote.total_ht
    total_vat = quote.total_vat
    total_ttc = quote.total_ttc

    po = PurchaseOrder.objects.create(
        customer=quote.customer,
        quote=quote,
        customer_name=quote.customer_name,
        customer_address=quote.customer_address,
        customer_ice=quote.customer_ice,
        customer_identifiant_fiscal=quote.customer_identifiant_fiscal,
        customer_registre_commerce=quote.customer_registre_commerce,
        customer_taxe_professionnelle=quote.customer_taxe_professionnelle,
        status="draft",
        payment_terms=quote.payment_terms,
        notes=f"Converti depuis {quote.ref}",
        total_ht=total_ht, total_vat=total_vat, total_ttc=total_ttc,
        created_by=request.user, tenant=tenant,
    )

    for ql in quote_lines:
        PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=ql.product,
            description=ql.description,
            qty=ql.qty,
            unit_price=ql.unit_price,
            vat_rate=ql.vat_rate,
            total_ht=ql.total_ht,
            total_vat=ql.total_vat,
            total_ttc=ql.total_ttc,
            tenant=tenant,
        )

    messages.success(request, f"BC {po.ref} créé depuis {quote.ref}.")
    return redirect("po-detail", pk=po.pk)


# ════════════════════════ PURCHASE ORDERS (BON DE COMMANDE) ════════════════════════

@login_required
def po_list(request):
    qs = PurchaseOrder.objects.select_related("customer", "created_by").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(ref__icontains=q) | Q(customer_name__icontains=q) | Q(customer__name__icontains=q) | Q(customer_po_ref__icontains=q))
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    return render(request, "commerce/po_list.html", {"pos": qs, "q": q, "status_filter": status})


@login_required
def po_detail(request, pk):
    po = _get_tenant_object_or_404(PurchaseOrder, pk, request.user)
    lines = po.lines.select_related("product").all()
    delivered_map = _po_delivered_quantities(po)
    delivery_notes = po.delivery_notes.select_related("created_by").all().order_by("-created_at")
    return render(request, "commerce/po_detail.html", {
        "po": po, "lines": lines,
        "delivered_map": delivered_map,
        "delivery_notes": delivery_notes,
        "tenant": request.user.tenant,
    })


@login_required
@role_required(*WRITE_ROLES)
def po_create(request):
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    default_vat = _get_vat_rate(tenant)
    quotes = Quote.objects.filter(status="accepted")
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        quote_id = request.POST.get("quote_id") or None
        customer_po_ref = request.POST.get("customer_po_ref", "")
        payment_terms = request.POST.get("payment_terms", "30 jours")
        notes = request.POST.get("notes", "")
        lines_data = _parse_lines(request)
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            total_ht, total_vat = _calc_lines(lines_data, default_vat)
            total_ttc = total_ht + total_vat
            cust = _gather_customer(customer_id)
            po = PurchaseOrder.objects.create(
                customer_id=customer_id, quote_id=quote_id,
                customer_po_ref=customer_po_ref, **cust,
                status="draft", payment_terms=payment_terms, notes=notes,
                total_ht=total_ht, total_vat=total_vat, total_ttc=total_ttc,
                created_by=request.user, tenant=tenant,
            )
            for ld in lines_data:
                PurchaseOrderLine.objects.create(purchase_order=po, tenant=tenant, **ld)
            messages.success(request, f"BC {po.ref} créé.")
            return redirect("po-detail", pk=po.pk)
    return render(request, "commerce/po_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": False, "quotes": quotes,
    })


@login_required
@role_required(*WRITE_ROLES)
def po_edit(request, pk):
    po = _get_tenant_object_or_404(PurchaseOrder, pk, request.user)
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    existing_lines = po.lines.select_related("product").all()
    if request.method == "POST":
        po.status = request.POST.get("status", po.status)
        po.customer_po_ref = request.POST.get("customer_po_ref", po.customer_po_ref)
        po.payment_terms = request.POST.get("payment_terms", po.payment_terms)
        po.notes = request.POST.get("notes", "")
        lines_data = _parse_lines(request)
        if lines_data:
            po.lines.all().delete()
            total_ht, total_vat = _calc_lines(lines_data, po.vat_rate or Decimal("0.20"))
            po.total_ht = total_ht
            po.total_vat = total_vat
            po.total_ttc = total_ht + total_vat
            for ld in lines_data:
                PurchaseOrderLine.objects.create(purchase_order=po, tenant=tenant, **ld)
        po.save()
        messages.success(request, f"BC {po.ref} mis à jour.")
        return redirect("po-detail", pk=po.pk)
    return render(request, "commerce/po_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": True, "po": po, "existing_lines": existing_lines, "quotes": [],
    })


@login_required
@role_required(*WRITE_ROLES)
def po_delete(request, pk):
    po = _get_tenant_object_or_404(PurchaseOrder, pk, request.user)
    if request.method == "POST":
        ref = po.ref
        po.delete()
        messages.success(request, f"BC {ref} supprimé.")
        return redirect("po-list")
    return render(request, "commerce/confirm_delete.html", {"object": po, "label": f"BC {po.ref}"})


@login_required
@role_required(*WRITE_ROLES)
def po_status_update(request, pk):
    po = _get_tenant_object_or_404(PurchaseOrder, pk, request.user)
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid_transitions = {
            "draft": ["confirmed", "cancelled"],
            "confirmed": ["in_progress", "cancelled"],
            "in_progress": ["delivered", "cancelled"],
        }
        allowed = valid_transitions.get(po.status, [])
        if new_status in allowed:
            po.status = new_status
            po.save()
            status_display = dict(PurchaseOrder.STATUS_CHOICES).get(new_status, new_status)
            messages.success(request, f"BC {po.ref} → {status_display}.")
        else:
            messages.error(request, f"Transition {po.status} → {new_status} non autorisée.")
    return redirect("po-detail", pk=po.pk)


# ════════════════════════ DELIVERY NOTES (BON DE LIVRAISON) ════════════════════════

@login_required
def bl_list(request):
    qs = DeliveryNote.objects.select_related("customer", "created_by").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(ref__icontains=q) | Q(customer_name__icontains=q) | Q(customer__name__icontains=q))
    return render(request, "commerce/bl_list.html", {"bls": qs, "q": q})


@login_required
def bl_detail(request, pk):
    bl = _get_tenant_object_or_404(DeliveryNote, pk, request.user)
    lines = bl.lines.select_related("product").all()
    return render(request, "commerce/bl_detail.html", {"bl": bl, "lines": lines})


@login_required
@role_required(*WRITE_ROLES)
def bl_create(request):
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    pos = PurchaseOrder.objects.filter(status__in=["confirmed", "in_progress"])
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        po_id = request.POST.get("po_id") or None
        delivery_date = request.POST.get("delivery_date") or None
        notes = request.POST.get("notes", "")
        lines_data = _parse_bl_lines(request)
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            cust = _gather_customer(customer_id)
            bl = DeliveryNote.objects.create(
                customer_id=customer_id, purchase_order_id=po_id,
                delivery_date=delivery_date, notes=notes,
                status="draft", created_by=request.user, tenant=tenant, **cust,
            )
            for ld in lines_data:
                DeliveryNoteLine.objects.create(delivery_note=bl, tenant=tenant, **ld)
            messages.success(request, f"BL {bl.ref} créé.")
            return redirect("bl-detail", pk=bl.pk)
    return render(request, "commerce/bl_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": False, "pos": pos,
    })


@login_required
@role_required(*WRITE_ROLES)
def bl_edit(request, pk):
    bl = _get_tenant_object_or_404(DeliveryNote, pk, request.user)
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    existing_lines = bl.lines.select_related("product").all()
    if request.method == "POST":
        bl.status = request.POST.get("status", bl.status)
        bl.delivery_date = request.POST.get("delivery_date") or bl.delivery_date
        bl.notes = request.POST.get("notes", "")
        lines_data = _parse_bl_lines(request)
        if lines_data:
            bl.lines.all().delete()
            for ld in lines_data:
                DeliveryNoteLine.objects.create(delivery_note=bl, tenant=tenant, **ld)
        bl.save()
        messages.success(request, f"BL {bl.ref} mis à jour.")
        return redirect("bl-detail", pk=bl.pk)
    return render(request, "commerce/bl_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": True, "bl": bl, "existing_lines": existing_lines, "pos": [],
    })


@login_required
@role_required(*WRITE_ROLES)
def bl_delete(request, pk):
    bl = _get_tenant_object_or_404(DeliveryNote, pk, request.user)
    if request.method == "POST":
        ref = bl.ref
        bl.delete()
        messages.success(request, f"BL {ref} supprimé.")
        return redirect("bl-list")
    return render(request, "commerce/confirm_delete.html", {"object": bl, "label": f"BL {bl.ref}"})


@login_required
@role_required(*WRITE_ROLES)
def po_convert_to_bl(request, pk):
    po = _get_tenant_object_or_404(PurchaseOrder, pk, request.user)
    if po.status not in ("confirmed", "in_progress"):
        messages.error(request, "Seuls les BC confirmés ou en cours peuvent générer un BL.")
        return redirect("po-detail", pk=po.pk)

    tenant = request.user.tenant
    po_lines = po.lines.select_related("product").all()
    delivered_map = _po_delivered_quantities(po)

    if request.method == "POST":
        delivery_date = request.POST.get("delivery_date") or None
        notes = request.POST.get("notes", "")
        lines_data = _parse_bl_lines(request)
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            cust = _gather_customer(po.customer_id)
            bl = DeliveryNote.objects.create(
                customer=po.customer, purchase_order=po,
                delivery_date=delivery_date, notes=notes,
                status="draft", created_by=request.user, tenant=tenant, **cust,
            )
            for ld in lines_data:
                DeliveryNoteLine.objects.create(delivery_note=bl, tenant=tenant, **ld)
            messages.success(request, f"BL {bl.ref} créé depuis {po.ref}.")
            return redirect("bl-detail", pk=bl.pk)

    form_lines = []
    for pl in po_lines:
        already = delivered_map.get(pl.product_id, Decimal("0"))
        remaining = pl.qty - already
        form_lines.append({
            "product": pl.product,
            "product_id": pl.product_id,
            "description": pl.description,
            "qty_ordered": pl.qty,
            "qty_delivered": remaining,
            "already_delivered": already,
            "remaining": remaining,
        })

    return render(request, "commerce/bl_form.html", {
        "po": po, "form_lines": form_lines,
        "editing": False, "from_po": True,
        "customers": Customer.objects.all(),
        "products": Product.objects.filter(is_active=True),
        "tenant": tenant,
    })


@login_required
@role_required(*WRITE_ROLES)
def bl_convert_to_invoice(request, pk):
    bl = _get_tenant_object_or_404(DeliveryNote, pk, request.user)
    if request.method != "POST":
        return redirect("bl-detail", pk=bl.pk)

    if bl.status == "draft":
        bl.status = "delivered"
        bl.save()

    from apps.finance.services import create_invoice
    tenant = request.user.tenant

    bl_lines = bl.lines.select_related("product").all()
    invoice_lines = []
    for bl_line in bl_lines:
        invoice_lines.append({
            "product_id": bl_line.product_id,
            "description": bl_line.description,
            "qty": bl_line.qty_delivered,
            "unit_price": Decimal("0"),
            "vat_rate": Decimal("0.20"),
        })

    if not invoice_lines:
        messages.error(request, "Aucune ligne à facturer.")
        return redirect("bl-detail", pk=bl.pk)

    from decimal import Decimal as D
    invoice = create_invoice(
        order_ref=bl.ref,
        lines=invoice_lines,
        user=request.user,
        customer_id=bl.customer_id,
        tenant=tenant,
    )

    bl.invoice = invoice
    bl.save()

    messages.success(request, f"Facture {invoice.invoice_ref} créée depuis BL {bl.ref}.")
    return redirect("invoice-detail", pk=invoice.pk)


# ════════════════════════ RETURN NOTES (BON DE RETOUR) ════════════════════════

@login_required
def brt_list(request):
    qs = ReturnNote.objects.select_related("customer", "created_by").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(ref__icontains=q) | Q(customer_name__icontains=q) | Q(customer__name__icontains=q))
    return render(request, "commerce/brt_list.html", {"brts": qs, "q": q})


@login_required
def brt_detail(request, pk):
    brt = _get_tenant_object_or_404(ReturnNote, pk, request.user)
    lines = brt.lines.select_related("product").all()
    return render(request, "commerce/brt_detail.html", {"brt": brt, "lines": lines})


@login_required
@role_required(*WRITE_ROLES)
def brt_create(request):
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        reason = request.POST.get("reason", "")
        product_ids = request.POST.getlist("line_product[]")
        qtys = request.POST.getlist("line_qty[]")
        reasons = request.POST.getlist("line_reason[]")
        lines_data = []
        for pid, qty, rsn in zip(product_ids, qtys, reasons):
            if pid and qty:
                lines_data.append({
                    "product_id": int(pid),
                    "qty": Decimal(str(qty)),
                    "reason": rsn,
                })
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            cust = _gather_customer(customer_id)
            brt = ReturnNote.objects.create(
                customer_id=customer_id, reason=reason,
                status="draft", created_by=request.user, tenant=tenant, **cust,
            )
            for ld in lines_data:
                ReturnNoteLine.objects.create(return_note=brt, tenant=tenant, **ld)
            messages.success(request, f"Bon de Retour {brt.ref} créé.")
            return redirect("brt-detail", pk=brt.pk)
    return render(request, "commerce/brt_form.html", {
        "customers": customers, "products": products, "editing": False,
    })


@login_required
@role_required(*WRITE_ROLES)
def brt_edit(request, pk):
    brt = _get_tenant_object_or_404(ReturnNote, pk, request.user)
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    existing_lines = brt.lines.select_related("product").all()
    if request.method == "POST":
        brt.status = request.POST.get("status", brt.status)
        brt.reason = request.POST.get("reason", brt.reason)
        product_ids = request.POST.getlist("line_product[]")
        qtys = request.POST.getlist("line_qty[]")
        reasons = request.POST.getlist("line_reason[]")
        if product_ids:
            brt.lines.all().delete()
            for pid, qty, rsn in zip(product_ids, qtys, reasons):
                if pid and qty:
                    ReturnNoteLine.objects.create(
                        return_note=brt, product_id=int(pid),
                        qty=Decimal(str(qty)), reason=rsn, tenant=tenant,
                    )
        brt.save()
        messages.success(request, f"Bon de Retour {brt.ref} mis à jour.")
        return redirect("brt-detail", pk=brt.pk)
    return render(request, "commerce/brt_form.html", {
        "customers": customers, "products": products,
        "editing": True, "brt": brt, "existing_lines": existing_lines,
    })


@login_required
@role_required(*WRITE_ROLES)
def brt_delete(request, pk):
    brt = _get_tenant_object_or_404(ReturnNote, pk, request.user)
    if request.method == "POST":
        ref = brt.ref
        brt.delete()
        messages.success(request, f"Bon de Retour {ref} supprimé.")
        return redirect("brt-list")
    return render(request, "commerce/confirm_delete.html", {"object": brt, "label": f"BRT {brt.ref}"})


# ════════════════════════ CREDIT NOTES (FACTURE D'AVOIR) ════════════════════════

@login_required
def cn_list(request):
    qs = CreditNote.objects.select_related("customer", "created_by").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(ref__icontains=q) | Q(customer_name__icontains=q) | Q(customer__name__icontains=q))
    return render(request, "commerce/cn_list.html", {"cns": qs, "q": q})


@login_required
def cn_detail(request, pk):
    cn = _get_tenant_object_or_404(CreditNote, pk, request.user)
    lines = cn.lines.select_related("product").all()
    return render(request, "commerce/cn_detail.html", {"cn": cn, "lines": lines, "tenant": request.user.tenant})


@login_required
@role_required(*WRITE_ROLES)
def cn_create(request):
    from apps.finance.models import Invoice
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    default_vat = _get_vat_rate(tenant)
    invoices = Invoice.objects.all()
    if request.method == "POST":
        customer_id = request.POST.get("customer_id") or None
        invoice_id = request.POST.get("invoice_id") or None
        reason = request.POST.get("reason", "")
        default_vat = Decimal(request.POST.get("default_vat_rate", "20")) / 100
        default_vat = _get_vat_rate(tenant, default_vat)
        lines_data = _parse_lines(request)
        if not lines_data:
            messages.error(request, "Ajoutez au moins un poste.")
        else:
            total_ht, total_vat = _calc_lines(lines_data, default_vat)
            total_ttc = total_ht + total_vat
            from apps.finance.number_to_french import number_to_french
            cust = _gather_customer(customer_id)
            cn = CreditNote.objects.create(
                customer_id=customer_id, original_invoice_id=invoice_id,
                reason=reason, **cust,
                status="draft",
                total_ht=total_ht, vat_rate=default_vat,
                total_vat=total_vat, total_ttc=total_ttc,
                amount_in_words=number_to_french(total_ttc),
                created_by=request.user, tenant=tenant,
            )
            for ld in lines_data:
                CreditNoteLine.objects.create(credit_note=cn, tenant=tenant, **ld)
            messages.success(request, f"Avoir {cn.ref} créé.")
            return redirect("cn-detail", pk=cn.pk)
    return render(request, "commerce/cn_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": False, "invoices": invoices,
    })


@login_required
@role_required(*WRITE_ROLES)
def cn_edit(request, pk):
    cn = _get_tenant_object_or_404(CreditNote, pk, request.user)
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    tenant = request.user.tenant
    existing_lines = cn.lines.select_related("product").all()
    from apps.finance.models import Invoice
    invoices = Invoice.objects.all()
    if request.method == "POST":
        cn.status = request.POST.get("status", cn.status)
        cn.reason = request.POST.get("reason", cn.reason)
        default_vat = Decimal(request.POST.get("default_vat_rate", "20")) / 100
        default_vat = _get_vat_rate(tenant, default_vat)
        cn.vat_rate = default_vat
        lines_data = _parse_lines(request)
        if lines_data:
            cn.lines.all().delete()
            total_ht, total_vat = _calc_lines(lines_data, default_vat)
            cn.total_ht = total_ht
            cn.total_vat = total_vat
            cn.total_ttc = total_ht + total_vat
            from apps.finance.number_to_french import number_to_french
            cn.amount_in_words = number_to_french(cn.total_ttc)
            for ld in lines_data:
                CreditNoteLine.objects.create(credit_note=cn, tenant=tenant, **ld)
        cn.save()
        messages.success(request, f"Avoir {cn.ref} mis à jour.")
        return redirect("cn-detail", pk=cn.pk)
    return render(request, "commerce/cn_form.html", {
        "customers": customers, "products": products, "tenant": tenant,
        "editing": True, "cn": cn, "existing_lines": existing_lines,
        "invoices": invoices,
    })


@login_required
@role_required(*WRITE_ROLES)
def cn_delete(request, pk):
    cn = _get_tenant_object_or_404(CreditNote, pk, request.user)
    if request.method == "POST":
        ref = cn.ref
        cn.delete()
        messages.success(request, f"Avoir {ref} supprimé.")
        return redirect("cn-list")
    return render(request, "commerce/confirm_delete.html", {"object": cn, "label": f"Avoir {cn.ref}"})
