from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "is_anonymized", "created_at")
    list_filter = ("is_anonymized",)
