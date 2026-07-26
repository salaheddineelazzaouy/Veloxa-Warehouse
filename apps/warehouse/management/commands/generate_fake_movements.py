import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from random import randint, choice
from faker import Faker
from apps.warehouse.models import Product, Location, StockMovement
from apps.tenants.models import Tenant
from apps.tenants.utils import bypass_tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])

User = get_user_model()


class Command(BaseCommand):
    help = "Generate N fake stock movements (inbound/outbound/adjustment)"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=200)
        parser.add_argument("--clear", action="store_true", help="Clear existing movements first")

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
                self.stdout.write(self.style.ERROR("No products found. Run seed_data or generate_fake_products first."))
                return

            locations = list(Location.objects.filter(is_active=True, tenant=tenant))
            if not locations:
                self.stdout.write(self.style.ERROR("No locations found. Run seed_data first."))
                return

            users = list(User.objects.filter(role="warehouse_manager", tenant=tenant))
            if not users:
                self.stdout.write(self.style.ERROR("No warehouse_manager users found. Run seed_data first."))
                return

            if clear:
                deleted = StockMovement.objects.filter(tenant=tenant).delete()
                self.stdout.write(f"Cleared {deleted[0]} movements.")

            now = timezone.now()
            ref_counter = 0

            with transaction.atomic():
                created = 0
                for _ in range(count):
                    product = choice(products)
                    location = choice(locations)
                    user = choice(users)
                    days_ago = randint(0, 365)
                    movement_date = now - timedelta(days=days_ago, hours=randint(0, 23), minutes=randint(0, 59))

                    movement_type = choice(["inbound", "inbound", "inbound", "outbound", "outbound", "adjustment"])

                    if movement_type == "inbound":
                        qty = randint(10, 500)
                        ref_prefix = "PO"
                        notes = [
                            f"Réception commande {fake.company()}",
                            f"Achat fournisseur — lot {fake.lexify('???-####')}",
                            f"Entrée stock magasin {choice(['A', 'B', 'C'])}",
                            f"Réapprovisionnement {fake.word()}",
                        ]
                    elif movement_type == "outbound":
                        qty = -(randint(1, 100))
                        ref_prefix = "SO"
                        notes = [
                            f"Vente {fake.company()} — BL-{fake.random_number(digits=4)}",
                            f"Commande client #{fake.random_number(digits=5)}",
                            f"Sortie pour {fake.city()}",
                            f"Expédition commande urgente",
                        ]
                    else:
                        qty = randint(-30, 30)
                        if qty == 0:
                            qty = choice([-5, -10, 5, 10])
                        ref_prefix = "ADJ"
                        notes = [
                            f"Inventaire physique — écart détecté",
                            f"Correction après comptage {fake.word()}",
                            f"Ajustement suite à contrôle qualité",
                            f"Règle inventaire {fake.date_this_year().strftime('%d/%m')}",
                        ]

                    ref_counter += 1
                    reference = f"{ref_prefix}-{movement_date.strftime('%Y%m%d')}-{ref_counter:04d}"

                    StockMovement.objects.create(
                        product=product,
                        qty=qty,
                        type=movement_type,
                        reference=reference,
                        note=choice(notes),
                        location=location,
                        created_by=user,
                        tenant=tenant,
                    )
                    created += 1

            self.stdout.write(self.style.SUCCESS(f"{created} fake movements created."))
