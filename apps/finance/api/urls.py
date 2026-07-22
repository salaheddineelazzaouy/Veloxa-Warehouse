from django.urls import path
from . import views

urlpatterns = [
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("invoices/create/", views.InvoiceCreateView.as_view(), name="invoice-create"),
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path("cogs/<int:product_id>/", views.COGSView.as_view(), name="cogs"),
]
