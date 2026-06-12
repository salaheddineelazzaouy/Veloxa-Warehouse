from django.urls import path
from . import views

urlpatterns = [
    path("", views.BackOrderListView.as_view(), name="backorder-list"),
    path("<int:pk>/fulfill/", views.FulfillBackOrderView.as_view(), name="backorder-fulfill"),
]
