from django.contrib import admin
from .models import (
    Quote, QuoteLine, PurchaseOrder, PurchaseOrderLine,
    DeliveryNote, DeliveryNoteLine, ReturnNote, ReturnNoteLine,
    CreditNote, CreditNoteLine,
)


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("ref", "customer", "status", "total_ttc", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "customer__name", "customer_name")
    inlines = [QuoteLineInline]


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("ref", "customer", "customer_po_ref", "status", "total_ttc", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "customer__name", "customer_name", "customer_po_ref")
    inlines = [PurchaseOrderLineInline]


class DeliveryNoteLineInline(admin.TabularInline):
    model = DeliveryNoteLine
    extra = 0


@admin.register(DeliveryNote)
class DeliveryNoteAdmin(admin.ModelAdmin):
    list_display = ("ref", "customer", "status", "delivery_date", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "customer__name", "customer_name")
    inlines = [DeliveryNoteLineInline]


class ReturnNoteLineInline(admin.TabularInline):
    model = ReturnNoteLine
    extra = 0


@admin.register(ReturnNote)
class ReturnNoteAdmin(admin.ModelAdmin):
    list_display = ("ref", "customer", "status", "return_date", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "customer__name", "customer_name")
    inlines = [ReturnNoteLineInline]


class CreditNoteLineInline(admin.TabularInline):
    model = CreditNoteLine
    extra = 0


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ("ref", "customer", "status", "total_ttc", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "customer__name", "customer_name")
    inlines = [CreditNoteLineInline]
