from django.urls import path
from . import views

urlpatterns = [
    path("customers/", views.CustomerListCreateView.as_view(), name="customer-list"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer-detail"),
    path("customers/<int:pk>/anonymize/", views.AnonymizeCustomerView.as_view(), name="customer-anonymize"),
]
