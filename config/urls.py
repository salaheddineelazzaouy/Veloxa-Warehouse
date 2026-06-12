from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from . import views

api_root = {
    "auth": "register, login, profile, token/refresh",
    "warehouse": "products, inbound, outbound, adjust, stock/<id>, reconcile, movements",
    "backorder": "list, <id>/fulfill",
    "finance": "invoices, invoices/create, cogs/<id>",
    "crm": "customers, customers/<id>/anonymize",
    "audit": "logs, anomalies",
}

def api_index(request):
    return JsonResponse({
        "message": "Veloxa Warehouse API v1",
        "endpoints": {f"api/{k}/": v for k, v in api_root.items()},
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_index, name="api-index"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/warehouse/", include("apps.warehouse.api.urls")),
    path("api/backorder/", include("apps.backorder.api.urls")),
    path("api/finance/", include("apps.finance.api.urls")),
    path("api/crm/", include("apps.crm.api.urls")),
    path("api/audit/", include("apps.audit.api.urls")),
    path("api/landing/", include("apps.landing.api.urls")),
    # Template views
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("", views.landing, name="landing"),
    path("landing/manage/", views.landing_manage, name="landing-manage"),
    path("landing/manage/feature/create/", views.landing_feature_create, name="landing-feature-create"),
    path("landing/manage/feature/<int:pk>/edit/", views.landing_feature_update, name="landing-feature-update"),
    path("landing/manage/feature/<int:pk>/delete/", views.landing_feature_delete, name="landing-feature-delete"),
    path("landing/manage/trust-card/create/", views.landing_trust_create, name="landing-trust-create"),
    path("landing/manage/trust-card/<int:pk>/edit/", views.landing_trust_update, name="landing-trust-update"),
    path("landing/manage/trust-card/<int:pk>/delete/", views.landing_trust_delete, name="landing-trust-delete"),
    path("landing/manage/pricing/create/", views.landing_pricing_create, name="landing-pricing-create"),
    path("landing/manage/pricing/<int:pk>/edit/", views.landing_pricing_update, name="landing-pricing-update"),
    path("landing/manage/pricing/<int:pk>/delete/", views.landing_pricing_delete, name="landing-pricing-delete"),
    path("landing/manage/page/create/", views.landing_page_create, name="landing-page-create"),
    path("landing/manage/page/<int:pk>/edit/", views.landing_page_update, name="landing-page-update"),
    path("landing/manage/page/<int:pk>/delete/", views.landing_page_delete, name="landing-page-delete"),
    path("landing/lead/", views.landing_lead_create, name="landing-lead-create"),
    path("about/", views.site_page, {"slug": "about"}, name="about"),
    path("legal/", views.site_page, {"slug": "legal"}, name="legal"),
    path("contact/", views.contact_page, name="contact"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # Product CRUD
    path("products/", views.product_list, name="product-list"),
    path("products/create/", views.product_create, name="product-create"),
    path("products/<int:pk>/", views.product_detail, name="product-detail"),
    path("products/<int:pk>/edit/", views.product_update, name="product-update"),
    path("products/<int:pk>/delete/", views.product_delete, name="product-delete"),

    # Location CRUD
    path("locations/", views.location_list, name="location-list"),
    path("locations/create/", views.location_create, name="location-create"),
    path("locations/<int:pk>/", views.location_detail, name="location-detail"),
    path("locations/<int:pk>/edit/", views.location_update, name="location-update"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location-delete"),

    # StockMovement (create / read only)
    path("movements/", views.movement_list, name="movement-list"),
    path("movements/create/", views.movement_create, name="movement-create"),
    path("movements/<int:pk>/", views.movement_detail, name="movement-detail"),

    # Customer CRUD
    path("customers/", views.customer_list, name="customer-list"),
    path("customers/create/", views.customer_create, name="customer-create"),
    path("customers/<int:pk>/", views.customer_detail, name="customer-detail"),
    path("customers/<int:pk>/edit/", views.customer_update, name="customer-update"),
    path("customers/<int:pk>/delete/", views.customer_delete, name="customer-delete"),

    # BackOrder CRUD
    path("backorders/", views.backorder_list, name="backorder-list"),
    path("backorders/create/", views.backorder_create, name="backorder-create"),
    path("backorders/<int:pk>/", views.backorder_detail, name="backorder-detail"),
    path("backorders/<int:pk>/edit/", views.backorder_update, name="backorder-update"),
    path("backorders/<int:pk>/delete/", views.backorder_delete, name="backorder-delete"),

    # Invoice (read / delete)
    path("invoices/", views.invoice_list, name="invoice-list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice-detail"),
    path("invoices/<int:pk>/delete/", views.invoice_delete, name="invoice-delete"),

    # AuditLog (read only)
    path("audit-logs/", views.audit_log_list, name="audit-log-list"),
    path("audit-logs/<int:pk>/", views.audit_log_detail, name="audit-log-detail"),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
