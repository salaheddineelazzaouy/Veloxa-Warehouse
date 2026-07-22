import logging
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from random import randint, choice, sample, uniform
from faker import Faker
from apps.warehouse.models import Product
from apps.crm.models import Customer
from apps.finance.models import Invoice, InvoiceLine
from apps.tenants.models import Tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])

User = get_user_model()


class Command(BaseCommand):
    help = "Generate N fake invoices with line items"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=100)
        parser.add_argument("--clear", action="store_true", help="Clear existing invoices first")

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR("No tenant found. Run seed_data first."))
            return

        products = list(Product.objects.filter(is_active=True, tenant=tenant))
        if not products:
            self.stdout.write(self.style.ERROR("No products found. Run seed_data first."))
            return

        customers = list(Customer.objects.filter(tenant=tenant))
        if not customers:
            self.stdout.write(self.style.ERROR("No customers found. Run seed_data first."))
            return

        users = list(User.objects.filter(tenant=tenant))
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Run seed_data first."))
            return

        if clear:
            deleted = InvoiceLine.objects.filter(tenant=tenant).delete()
            self.stdout.write(f"Cleared {deleted[0]} invoice lines.")
            deleted = Invoice.objects.filter(tenant=tenant).delete()
            self.stdout.write(f"Cleared {deleted[0]} invoices.")

        now = timezone.now()
        inv_counter = 0

        with transaction.atomic():
            created = 0
            for _ in range(count):
                inv_counter += 1
                days_ago = randint(0, 365)
                inv_date = now - timedelta(days=days_ago)
                order_ref = f"SO-{inv_date.strftime('%Y%m%d')}-{randint(100, 999)}"
                invoice_ref = f"INV-{order_ref}"

                customer = choice(customers)
                created_by = choice(users)
                source = choice(["pos", "pos", "pos", "api", "web"])

                invoice = Invoice.objects.create(
                    invoice_ref=invoice_ref,
                    order_ref=order_ref,
                    customer=customer,
                    customer_ice=customer.ice or "",
                    customer_identifiant_fiscal=getattr(customer, "identifiant_fiscal", "") or "",
                    customer_taxe_professionnelle=getattr(customer, "taxe_professionnelle", "") or "",
                    customer_registre_commerce=getattr(customer, "registre_commerce", "") or "",
                    total=Decimal("0"),
                    source=source,
                    created_by=created_by,
                    tenant=tenant,
                )

                total = Decimal("0")
                line_products = sample(products, min(randint(1, 6), len(products)))
                for product in line_products:
                    qty = randint(1, 50)
                    markup = Decimal(str(round(uniform(1.1, 1.5), 2)))
                    unit_price = (product.cost_price * markup).quantize(Decimal("0.01"))
                    line_total = Decimal(str(qty)) * unit_price
                    InvoiceLine.objects.create(
                        invoice=invoice,
                        product=product,
                        qty=qty,
                        unit_price=unit_price,
                        total=line_total,
                        tenant=tenant,
                    )
                    total += line_total

                invoice.total = total.quantize(Decimal("0.01"))
                invoice.save(update_fields=["total"])
                created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} fake invoices created."))
