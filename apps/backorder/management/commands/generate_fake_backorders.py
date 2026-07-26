import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from random import randint, choice
from faker import Faker
from apps.warehouse.models import Product
from apps.backorder.models import BackOrder
from apps.tenants.models import Tenant
from apps.tenants.utils import bypass_tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])

User = get_user_model()


class Command(BaseCommand):
    help = "Generate N fake backorders"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=50)
        parser.add_argument("--clear", action="store_true", help="Clear existing backorders first")

    def handle(self, *args, **options):
        with bypass_tenant():
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

            users = list(User.objects.filter(tenant=tenant))
            if not users:
                self.stdout.write(self.style.ERROR("No users found. Run seed_data first."))
                return

            if clear:
                deleted = BackOrder.objects.filter(tenant=tenant).delete()
                self.stdout.write(f"Cleared {deleted[0]} backorders.")

            now = timezone.now()
            statuses = ["open", "open", "open", "partially_fulfilled", "partially_fulfilled", "closed"]
            cities = ["Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir", "Oujda", "Kenitra"]

            with transaction.atomic():
                created = 0
                for _ in range(count):
                    product = choice(products)
                    user = choice(users)
                    status = choice(statuses)
                    qty = randint(5, 100)

                    if status == "closed":
                        qty_fulfilled = qty
                    elif status == "partially_fulfilled":
                        qty_fulfilled = randint(1, qty - 1)
                    else:
                        qty_fulfilled = 0

                    days_ago = randint(0, 180)
                    created_at = now - timedelta(days=days_ago)

                    bo = BackOrder(
                        product=product,
                        qty=qty,
                        qty_fulfilled=qty_fulfilled,
                        status=status,
                        sales_order_ref=f"SO-BO-{created_at.strftime('%Y%m%d')}-{randint(100, 999)}",
                        created_by=user,
                        tenant=tenant,
                    )
                    bo.save()
                    created += 1

            self.stdout.write(self.style.SUCCESS(f"{created} fake backorders created."))
