from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from apps.warehouse.models import Product, Location, StockMovement, Category, Unit
from apps.backorder.models import BackOrder
from apps.crm.models import Customer
from apps.finance.models import Invoice
from apps.audit.models import AuditLog
from apps.landing.models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage

User = get_user_model()


def landing(request):
    ctx = {
        "hero": HeroSection.objects.filter(is_active=True).first(),
        "features": Feature.objects.filter(is_active=True),
        "trust_cards": TrustCard.objects.filter(is_active=True),
        "pricing_plans": PricingPlan.objects.filter(is_active=True),
        "compliance": ComplianceSection.objects.filter(is_active=True).first(),
        "cta": CTASection.objects.filter(is_active=True).first(),
    }
    return render(request, "landing.html", ctx)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        error = "Invalid credentials"
    return render(request, "login.html", {"error": error})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "signup.html")


def app_view(request):
    import os
    from django.http import HttpResponse
    from django.conf import settings
    index_path = settings.BASE_DIR.parent / "frontend" / "dist" / "index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        return HttpResponse(html)
    return render(request, "app.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def profile_view(request):
    from apps.subscriptions.models import Subscription
    sub = Subscription.objects.filter(user=request.user).order_by('-created_at').first()
    email_form = None
    password_form = None
    if request.method == "POST":
        if "update_email" in request.POST:
            new_email = request.POST.get("email", "").strip()
            if new_email:
                if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                    messages.error(request, "Email already in use.")
                else:
                    request.user.email = new_email
                    request.user.save(update_fields=["email"])
                    messages.success(request, "Email updated.")
            else:
                messages.error(request, "Email cannot be empty.")
            return redirect("profile")
        elif "update_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed.")
                return redirect("profile")
            else:
                for errors in password_form.errors.values():
                    for err in errors:
                        messages.error(request, err)
                return redirect("profile")
    return render(request, "profile.html", {"email_form": email_form, "password_form": password_form, "subscription": sub})

@login_required
def dashboard(request):
    from apps.subscriptions.models import Subscription

    sub = Subscription.objects.filter(user=request.user).order_by('-created_at').first()
    stats = {
        "products": Product.objects.count(),
        "locations": Location.objects.count(),
        "movements": StockMovement.objects.count(),
        "customers": Customer.objects.count(),
        "backorders": BackOrder.objects.count(),
        "open_backorders": BackOrder.objects.filter(status__in=["open", "partially_fulfilled"]).count(),
        "invoices": Invoice.objects.count(),
        "audit_logs": AuditLog.objects.count(),
        "users": User.objects.count(),
    }
    return render(request, "dashboard.html", {"stats": stats, "subscription": sub})

# ────────────────────────────── Category ──────────────────────────────

@login_required
def category_list(request):
    return render(request, "categories.html", {"categories": Category.objects.all()})

@login_required
def category_detail(request, pk):
    from django.db.models import Sum
    cat = get_object_or_404(Category, pk=pk)
    products = Product.objects.filter(category=cat).select_related("unit")
    for p in products:
        p.net_stock = StockMovement.objects.filter(product=p).aggregate(Sum("qty"))["qty__sum"] or 0
    return render(request, "category_detail.html", {"category": cat, "products": products})

@login_required
def category_create(request):
    if request.method == "POST":
        Category.objects.create(
            name=request.POST["name"],
            description=request.POST.get("description", ""),
            is_active=request.POST.get("is_active") == "on",
            tenant=request.user.tenant,
        )
        messages.success(request, "Category created.")
        return redirect("category-list")
    return render(request, "category_form.html", {"category": None})

@login_required
def category_update(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        cat.name = request.POST["name"]
        cat.description = request.POST.get("description", "")
        cat.is_active = request.POST.get("is_active") == "on"
        cat.save()
        messages.success(request, "Category updated.")
        return redirect("category-list")
    return render(request, "category_form.html", {"category": cat})

@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            cat.delete()
            messages.success(request, "Category deleted.")
            return redirect("category-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            messages.error(request, f"Cannot delete — referenced by {', '.join(sorted(models))}.")
            return redirect("category-list")
    return render(request, "category_confirm_delete.html", {"object": cat, "label": f"Category {cat.name}"})

# ────────────────────────────── Product ──────────────────────────────

@login_required
def product_list(request):
    return render(request, "products.html", {"products": Product.objects.all()})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = StockMovement.objects.filter(product=product).select_related("location", "created_by")
    net = movements.aggregate(Sum("qty"))["qty__sum"] or 0
    return render(request, "product_detail.html", {"product": product, "movements": movements, "net_stock": net})

@login_required
def product_create(request):
    if request.method == "POST":
        cat_id = request.POST.get("category") or None
        unit_id = request.POST.get("unit") or None
        product = Product.objects.create(
            sku=request.POST["sku"], name=request.POST["name"],
            description=request.POST.get("description", ""),
            category_id=cat_id, unit_id=unit_id,
            cost_price=request.POST["cost_price"],
            is_active=request.POST.get("is_active") == "on",
            tenant=request.user.tenant,
        )
        messages.success(request, "Product created.")
        return redirect("product-detail", pk=product.pk)
    return render(request, "product_form.html", {
        "product": None,
        "categories": Category.objects.filter(is_active=True),
        "units": Unit.objects.filter(is_active=True),
    })

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        cat_id = request.POST.get("category") or None
        unit_id = request.POST.get("unit") or None
        product.sku = request.POST["sku"]
        product.name = request.POST["name"]
        product.description = request.POST.get("description", "")
        product.category_id = cat_id
        product.unit_id = unit_id
        product.cost_price = request.POST["cost_price"]
        product.is_active = request.POST.get("is_active") == "on"
        product.save()
        messages.success(request, "Product updated.")
        return redirect("product-detail", pk=product.pk)
    return render(request, "product_form.html", {
        "product": product,
        "categories": Category.objects.filter(is_active=True),
        "units": Unit.objects.filter(is_active=True),
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
            messages.success(request, "Product deleted.")
            return redirect("product-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            msg = f"Cannot delete — referenced by {', '.join(sorted(models))}."
            messages.error(request, msg)
            return redirect("product-detail", pk=pk)
    return render(request, "product_confirm_delete.html", {"object": product, "label": f"Product {product.sku}"})

# ────────────────────────────── Location ──────────────────────────────

@login_required
def location_list(request):
    return render(request, "locations.html", {"locations": Location.objects.all()})

@login_required
def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, "location_detail.html", {"location": location})

@login_required
def location_create(request):
    if request.method == "POST":
        Location.objects.create(
            code=request.POST["code"], name=request.POST["name"],
            is_active=request.POST.get("is_active") == "on",
            tenant=request.user.tenant,
        )
        messages.success(request, "Location created.")
        return redirect("location-list")
    return render(request, "location_form.html", {"location": None})

@login_required
def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == "POST":
        location.code = request.POST["code"]
        location.name = request.POST["name"]
        location.is_active = request.POST.get("is_active") == "on"
        location.save()
        messages.success(request, "Location updated.")
        return redirect("location-list")
    return render(request, "location_form.html", {"location": location})

@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == "POST":
        try:
            location.delete()
            messages.success(request, "Location deleted.")
            return redirect("location-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            messages.error(request, f"Cannot delete — referenced by {', '.join(sorted(models))}.")
            return redirect("location-list")
    return render(request, "location_confirm_delete.html", {"object": location, "label": f"Location {location.code}"})

# ────────────────────────────── StockMovement ──────────────────────────────

@login_required
def movement_list(request):
    return render(request, "movements.html", {"movements": StockMovement.objects.select_related("product", "location", "created_by").all()[:100]})

@login_required
def movement_detail(request, pk):
    m = get_object_or_404(StockMovement.objects.select_related("product", "location", "created_by"), pk=pk)
    return render(request, "movement_detail.html", {"movement": m})

@login_required
def movement_create(request):
    if request.method == "POST":
        product = get_object_or_404(Product, pk=request.POST["product"])
        qty = int(request.POST["qty"])
        mtype = request.POST["type"]
        if mtype == "outbound" and qty > 0:
            qty = -qty
        location_id = request.POST.get("location") or None
        location = Location.objects.filter(pk=location_id).first() if location_id else None
        StockMovement.objects.create(
            product=product, qty=qty, type=mtype,
            reference=request.POST["reference"],
            note=request.POST.get("note", ""),
            location=location, created_by=request.user,
            tenant=request.user.tenant,
        )
        messages.success(request, "Movement recorded.")
        return redirect("movement-list")
    products = Product.objects.filter(is_active=True)
    locations = Location.objects.filter(is_active=True)
    return render(request, "movement_form.html", {"products": products, "locations": locations})

# ────────────────────────────── Customer ──────────────────────────────

@login_required
def customer_list(request):
    return render(request, "customers.html", {"customers": Customer.objects.all()})

@login_required
def customer_detail(request, pk):
    from django.db.models import Sum, Count
    from decimal import Decimal
    from apps.finance.models import Invoice
    customer = get_object_or_404(Customer, pk=pk)
    invoices = Invoice.objects.filter(customer=customer).select_related("created_by").order_by("-created_at")
    invoice_count = invoices.count()
    agg = invoices.aggregate(total=Sum("total"))
    total_revenue = agg["total"] or Decimal("0")
    avg_invoice = (total_revenue / invoice_count).quantize(Decimal("0.01")) if invoice_count else Decimal("0")
    return render(request, "customer_detail.html", {
        "customer": customer,
        "invoices": invoices,
        "invoice_count": invoice_count,
        "total_revenue": total_revenue,
        "avg_invoice": avg_invoice,
    })

@login_required
def customer_create(request):
    if request.method == "POST":
        Customer.objects.create(
            tenant=request.user.tenant,
            name=request.POST["name"], phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""), address=request.POST.get("address", ""),
            tax_id=request.POST.get("tax_id", ""),
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, "Customer created.")
        return redirect("customer-list")
    return render(request, "customer_form.html", {"customer": None})

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.name = request.POST["name"]
        customer.phone = request.POST.get("phone", "")
        customer.email = request.POST.get("email", "")
        customer.address = request.POST.get("address", "")
        customer.tax_id = request.POST.get("tax_id", "")
        customer.is_active = request.POST.get("is_active") == "on"
        customer.save()
        messages.success(request, "Customer updated.")
        return redirect("customer-list")
    return render(request, "customer_form.html", {"customer": customer})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        try:
            customer.delete()
            messages.success(request, "Customer deleted.")
            return redirect("customer-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            messages.error(request, f"Cannot delete — referenced by {', '.join(sorted(models))}.")
            return redirect("customer-list")
    return render(request, "customer_confirm_delete.html", {"object": customer, "label": f"Customer {customer.name}"})

# ────────────────────────────── BackOrder ──────────────────────────────

@login_required
def backorder_list(request):
    from django.db.models import Q
    qs = BackOrder.objects.select_related("product", "created_by").all()

    status = request.GET.get("status", "")
    search = request.GET.get("q", "")

    if status in ("open", "partially_fulfilled", "closed"):
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(
            Q(product__sku__icontains=search)
            | Q(product__name__icontains=search)
            | Q(sales_order_ref__icontains=search)
        )

    stats = {
        "total": BackOrder.objects.count(),
        "open": BackOrder.objects.filter(status="open").count(),
        "partial": BackOrder.objects.filter(status="partially_fulfilled").count(),
        "closed": BackOrder.objects.filter(status="closed").count(),
    }

    return render(request, "backorders.html", {
        "backorders": qs,
        "stats": stats,
        "active_status": status,
        "search_query": search,
    })

@login_required
def backorder_detail(request, pk):
    bo = get_object_or_404(BackOrder.objects.select_related("product", "created_by"), pk=pk)
    return render(request, "backorder_detail.html", {"backorder": bo})

@login_required
def backorder_create(request):
    if request.method == "POST":
        BackOrder.objects.create(
            product_id=request.POST["product"], qty=request.POST["qty"],
            sales_order_ref=request.POST.get("sales_order_ref", ""),
            created_by=request.user,
            tenant=request.user.tenant,
        )
        messages.success(request, "Backorder created.")
        return redirect("backorder-list")
    products = Product.objects.filter(is_active=True)
    return render(request, "backorder_form.html", {"backorder": None, "products": products})

@login_required
def backorder_update(request, pk):
    bo = get_object_or_404(BackOrder, pk=pk)
    if request.method == "POST":
        bo.qty = request.POST["qty"]
        bo.sales_order_ref = request.POST.get("sales_order_ref", "")
        bo.save()
        messages.success(request, "Backorder updated.")
        return redirect("backorder-detail", pk=bo.pk)
    products = Product.objects.filter(is_active=True)
    return render(request, "backorder_form.html", {"backorder": bo, "products": products})

@login_required
def backorder_delete(request, pk):
    bo = get_object_or_404(BackOrder, pk=pk)
    if request.method == "POST":
        try:
            bo.delete()
            messages.success(request, "Backorder deleted.")
            return redirect("backorder-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            messages.error(request, f"Cannot delete — referenced by {', '.join(sorted(models))}.")
            return redirect("backorder-list")
    return render(request, "backorder_confirm_delete.html", {"object": bo, "label": f"BackOrder BO-{bo.id}"})

# ────────────────────────────── Invoice ──────────────────────────────

@login_required
def invoice_create(request):
    from apps.finance.services import create_invoice
    customers = Customer.objects.all()
    products = Product.objects.filter(is_active=True)
    if request.method == "POST":
        order_ref = request.POST["order_ref"]
        customer_id = request.POST.get("customer_id") or None
        product_ids = request.POST.getlist("product_id[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("unit_price[]")
        lines = []
        for pid, qty, price in zip(product_ids, qtys, prices):
            if pid and qty and price:
                lines.append({
                    "product_id": int(pid),
                    "qty": int(qty),
                    "unit_price": price,
                })
        if not lines:
            messages.error(request, "Add at least one line item.")
        else:
            try:
                create_invoice(order_ref, lines, request.user, customer_id, tenant=request.user.tenant)
                messages.success(request, "Invoice created.")
                return redirect("invoice-list")
            except Exception as e:
                messages.error(request, f"Error: {e}")
    return render(request, "invoice_form.html", {
        "customers": customers,
        "products": products,
    })

@login_required
def invoice_list(request):
    return render(request, "invoices.html", {"invoices": Invoice.objects.select_related("customer", "created_by").all()})

@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related("customer", "created_by"), pk=pk)
    lines = inv.lines.select_related("product").all()
    return render(request, "invoice_detail.html", {"invoice": inv, "lines": lines})

@login_required
def invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        try:
            inv.delete()
            messages.success(request, "Invoice deleted.")
            return redirect("invoice-list")
        except ProtectedError as e:
            models = set(type(obj)._meta.verbose_name for obj in e.protected_objects)
            messages.error(request, f"Cannot delete — referenced by {', '.join(sorted(models))}.")
            return redirect("invoice-list")
    return render(request, "invoice_confirm_delete.html", {"object": inv, "label": f"Invoice {inv.invoice_ref}"})

# ────────────────────────────── AuditLog ──────────────────────────────

@login_required
def audit_log_list(request):
    return render(request, "audit_logs.html", {"audit_logs": AuditLog.objects.select_related("user").all()[:100]})

@login_required
def audit_log_detail(request, pk):
    log = get_object_or_404(AuditLog.objects.select_related("user"), pk=pk)
    return render(request, "audit_log_detail.html", {"log": log})


# ────────────────────────────── Landing Content Management ──────────────────────────────

@login_required
def landing_manage(request):
    if request.method == "POST":
        section = request.POST.get("_section", "")
        if section == "hero":
            obj = HeroSection.objects.filter(is_active=True).first() or HeroSection()
            for f in ["headline", "subtitle", "cta_text", "cta_link", "secondary_cta_text", "secondary_cta_link"]:
                if f in request.POST:
                    setattr(obj, f, request.POST[f])
            obj.save()
            messages.success(request, "Hero section updated.")
        elif section == "cta":
            obj = CTASection.objects.filter(is_active=True).first() or CTASection()
            for f in ["headline", "subtitle", "button_text", "placeholder", "footnote"]:
                if f in request.POST:
                    setattr(obj, f, request.POST[f])
            obj.save()
            messages.success(request, "CTA section updated.")
        elif section == "compliance":
            obj = ComplianceSection.objects.filter(is_active=True).first() or ComplianceSection()
            for f in ["title", "law_title", "items"]:
                if f in request.POST:
                    setattr(obj, f, request.POST[f])
            obj.save()
            messages.success(request, "Compliance section updated.")
        return redirect("landing-manage")

    return render(request, "landing_manage.html", {
        "hero": HeroSection.objects.filter(is_active=True).first(),
        "features": Feature.objects.filter(is_active=True),
        "trust_cards": TrustCard.objects.filter(is_active=True),
        "pricing_plans": PricingPlan.objects.filter(is_active=True),
        "compliance": ComplianceSection.objects.filter(is_active=True).first(),
        "cta": CTASection.objects.filter(is_active=True).first(),
        "pages": SitePage.objects.filter(is_active=True),
        "leads": LandingLead.objects.all()[:20],
    })


@login_required
def landing_feature_create(request):
    if request.method == "POST":
        Feature.objects.create(
            title=request.POST["title"],
            description=request.POST["description"],
            icon_class=request.POST.get("icon_class", "fas fa-book"),
            icon_bg=request.POST.get("icon_bg", "#2563eb"),
            icon_bg_end=request.POST.get("icon_bg_end", "#1d4ed8"),
            order=request.POST.get("order", 0),
        )
        messages.success(request, "Feature created.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Feature", "fields": [
        ("title", "text", "Title"),
        ("description", "textarea", "Description"),
        ("icon_class", "text", "Icon Class (e.g. fas fa-book)"),
        ("icon_bg", "text", "Icon BG Start (e.g. #2563eb)"),
        ("icon_bg_end", "text", "Icon BG End (e.g. #1d4ed8)"),
        ("order", "number", "Order"),
    ]})


@login_required
def landing_feature_update(request, pk):
    obj = get_object_or_404(Feature, pk=pk)
    if request.method == "POST":
        obj.title = request.POST["title"]
        obj.description = request.POST["description"]
        obj.icon_class = request.POST.get("icon_class", obj.icon_class)
        obj.icon_bg = request.POST.get("icon_bg", obj.icon_bg)
        obj.icon_bg_end = request.POST.get("icon_bg_end", obj.icon_bg_end)
        obj.order = request.POST.get("order", obj.order)
        obj.save()
        messages.success(request, "Feature updated.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Feature", "fields": [
        ("title", "text", "Title", obj.title),
        ("description", "textarea", "Description", obj.description),
        ("icon_class", "text", "Icon Class", obj.icon_class),
        ("icon_bg", "text", "Icon BG Start", obj.icon_bg),
        ("icon_bg_end", "text", "Icon BG End", obj.icon_bg_end),
        ("order", "number", "Order", obj.order),
    ]})


@login_required
def landing_feature_delete(request, pk):
    obj = get_object_or_404(Feature, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Feature deleted.")
    return redirect("landing-manage")


@login_required
def landing_trust_create(request):
    if request.method == "POST":
        TrustCard.objects.create(
            title=request.POST["title"],
            description=request.POST["description"],
            icon_class=request.POST.get("icon_class", "fas fa-shield-alt"),
            icon_bg=request.POST.get("icon_bg", "linear-gradient(135deg,#2563eb,#1d4ed8)"),
            order=request.POST.get("order", 0),
        )
        messages.success(request, "Trust card created.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Trust Card", "fields": [
        ("title", "text", "Title"),
        ("description", "textarea", "Description"),
        ("icon_class", "text", "Icon Class"),
        ("icon_bg", "text", "Icon BG (CSS gradient)"),
        ("order", "number", "Order"),
    ]})


@login_required
def landing_trust_update(request, pk):
    obj = get_object_or_404(TrustCard, pk=pk)
    if request.method == "POST":
        obj.title = request.POST["title"]
        obj.description = request.POST["description"]
        obj.icon_class = request.POST.get("icon_class", obj.icon_class)
        obj.icon_bg = request.POST.get("icon_bg", obj.icon_bg)
        obj.order = request.POST.get("order", obj.order)
        obj.save()
        messages.success(request, "Trust card updated.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Trust Card", "fields": [
        ("title", "text", "Title", obj.title),
        ("description", "textarea", "Description", obj.description),
        ("icon_class", "text", "Icon Class", obj.icon_class),
        ("icon_bg", "text", "Icon BG", obj.icon_bg),
        ("order", "number", "Order", obj.order),
    ]})


@login_required
def landing_trust_delete(request, pk):
    obj = get_object_or_404(TrustCard, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Trust card deleted.")
    return redirect("landing-manage")


@login_required
def landing_pricing_create(request):
    if request.method == "POST":
        PricingPlan.objects.create(
            name=request.POST["name"],
            price=request.POST["price"],
            period=request.POST["period"],
            features=request.POST["features"],
            is_popular=request.POST.get("is_popular") == "on",
            button_text=request.POST.get("button_text", "Request demo"),
            button_class=request.POST.get("button_class", "btn-outline"),
            order=request.POST.get("order", 0),
        )
        messages.success(request, "Pricing plan created.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Pricing Plan", "fields": [
        ("name", "text", "Plan Name"),
        ("price", "text", "Price (e.g. MAD 2,500)"),
        ("period", "text", "Period (e.g. Up to 5 users)"),
        ("features", "textarea", "Features (one per line)"),
        ("is_popular", "checkbox", "Popular?"),
        ("button_text", "text", "Button Text"),
        ("button_class", "text", "Button Class (btn-primary / btn-outline)"),
        ("order", "number", "Order"),
    ]})


@login_required
def landing_pricing_update(request, pk):
    obj = get_object_or_404(PricingPlan, pk=pk)
    if request.method == "POST":
        obj.name = request.POST["name"]
        obj.price = request.POST["price"]
        obj.period = request.POST["period"]
        obj.features = request.POST["features"]
        obj.is_popular = request.POST.get("is_popular") == "on"
        obj.button_text = request.POST.get("button_text", obj.button_text)
        obj.button_class = request.POST.get("button_class", obj.button_class)
        obj.order = request.POST.get("order", obj.order)
        obj.save()
        messages.success(request, "Pricing plan updated.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Pricing Plan", "fields": [
        ("name", "text", "Plan Name", obj.name),
        ("price", "text", "Price", obj.price),
        ("period", "text", "Period", obj.period),
        ("features", "textarea", "Features (one per line)", obj.features),
        ("is_popular", "checkbox", "Popular?", obj.is_popular),
        ("button_text", "text", "Button Text", obj.button_text),
        ("button_class", "text", "Button Class", obj.button_class),
        ("order", "number", "Order", obj.order),
    ]})


@login_required
def landing_pricing_delete(request, pk):
    obj = get_object_or_404(PricingPlan, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Pricing plan deleted.")
    return redirect("landing-manage")


@login_required
def landing_page_create(request):
    if request.method == "POST":
        SitePage.objects.create(
            slug=request.POST["slug"],
            title=request.POST["title"],
            content=request.POST["content"],
        )
        messages.success(request, "Page created.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Site Page", "fields": [
        ("slug", "text", "Slug (e.g. about, careers)"),
        ("title", "text", "Title"),
        ("content", "ckeditor", "Content"),
    ]})


@login_required
def landing_page_update(request, pk):
    obj = get_object_or_404(SitePage, pk=pk)
    if request.method == "POST":
        obj.slug = request.POST["slug"]
        obj.title = request.POST["title"]
        obj.content = request.POST["content"]
        obj.save()
        messages.success(request, "Page updated.")
        return redirect("landing-manage")
    return render(request, "landing_form.html", {"model_type": "Site Page", "fields": [
        ("slug", "text", "Slug", obj.slug),
        ("title", "text", "Title", obj.title),
        ("content", "ckeditor", "Content", obj.content),
    ]})


@login_required
def landing_page_delete(request, pk):
    obj = get_object_or_404(SitePage, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Page deleted.")
    return redirect("landing-manage")


def landing_lead_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        company = request.POST.get("company", "")
        message = request.POST.get("message", "")
        if email:
            LandingLead.objects.create(name=name, email=email, company=company, message=message)
            messages.success(request, "Thank you! We'll be in touch soon.")
        else:
            messages.error(request, "Email is required.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    return redirect("/")


def site_page(request, slug):
    page = get_object_or_404(SitePage, slug=slug, is_active=True)
    return render(request, "site_page.html", {"page": page})


def contact_page(request):
    return render(request, "contact.html")
