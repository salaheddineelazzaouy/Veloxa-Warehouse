from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.ProductListCreateView.as_view(), name="product-list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("inbound/", views.InboundView.as_view(), name="inbound"),
    path("outbound/", views.OutboundView.as_view(), name="outbound"),
    path("adjust/", views.AdjustmentView.as_view(), name="adjustment"),
    path("stock/<int:product_id>/", views.StockCheckView.as_view(), name="stock-check"),
    path("reconcile/", views.ReconcileView.as_view(), name="reconcile"),
    path("movements/", views.MovementListView.as_view(), name="movement-list"),
    path("dashboard/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
    path("reservations/", views.ReservationListView.as_view(), name="reservation-list"),
    path("reservations/create/", views.ReserveView.as_view(), name="reservation-create"),
    path("reservations/<int:pk>/confirm/", views.ConfirmReservationView.as_view(), name="reservation-confirm"),
    path("reservations/<int:pk>/release/", views.ReleaseReservationView.as_view(), name="reservation-release"),
]
