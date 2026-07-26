from django.urls import path
from . import views

urlpatterns = [
    # Devis
    path("quotes/", views.quote_list, name="quote-list"),
    path("quotes/create/", views.quote_create, name="quote-create"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote-detail"),
    path("quotes/<int:pk>/edit/", views.quote_edit, name="quote-edit"),
    path("quotes/<int:pk>/delete/", views.quote_delete, name="quote-delete"),
    path("quotes/<int:pk>/accept/", views.quote_accept, name="quote-accept"),
    path("quotes/<int:pk>/reject/", views.quote_reject, name="quote-reject"),
    path("quotes/<int:pk>/convert-to-po/", views.quote_convert_to_po, name="quote-convert-to-po"),
    # Bon de Commande
    path("orders/", views.po_list, name="po-list"),
    path("orders/create/", views.po_create, name="po-create"),
    path("orders/<int:pk>/", views.po_detail, name="po-detail"),
    path("orders/<int:pk>/edit/", views.po_edit, name="po-edit"),
    path("orders/<int:pk>/delete/", views.po_delete, name="po-delete"),
    path("orders/<int:pk>/status/", views.po_status_update, name="po-status-update"),
    path("orders/<int:pk>/convert-to-bl/", views.po_convert_to_bl, name="po-convert-to-bl"),
    # Bon de Livraison
    path("deliveries/", views.bl_list, name="bl-list"),
    path("deliveries/create/", views.bl_create, name="bl-create"),
    path("deliveries/<int:pk>/", views.bl_detail, name="bl-detail"),
    path("deliveries/<int:pk>/edit/", views.bl_edit, name="bl-edit"),
    path("deliveries/<int:pk>/delete/", views.bl_delete, name="bl-delete"),
    path("deliveries/<int:pk>/convert-to-invoice/", views.bl_convert_to_invoice, name="bl-convert-to-invoice"),
    # Bon de Retour
    path("returns/", views.brt_list, name="brt-list"),
    path("returns/create/", views.brt_create, name="brt-create"),
    path("returns/<int:pk>/", views.brt_detail, name="brt-detail"),
    path("returns/<int:pk>/edit/", views.brt_edit, name="brt-edit"),
    path("returns/<int:pk>/delete/", views.brt_delete, name="brt-delete"),
    # Facture d'Avoir
    path("credit-notes/", views.cn_list, name="cn-list"),
    path("credit-notes/create/", views.cn_create, name="cn-create"),
    path("credit-notes/<int:pk>/", views.cn_detail, name="cn-detail"),
    path("credit-notes/<int:pk>/edit/", views.cn_edit, name="cn-edit"),
    path("credit-notes/<int:pk>/delete/", views.cn_delete, name="cn-delete"),
]
