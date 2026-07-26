import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from random import randint, choice, uniform
from faker import Faker
from apps.warehouse.models import Product, Category, Unit
from apps.tenants.models import Tenant
from apps.tenants.utils import bypass_tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])


class Command(BaseCommand):
    help = "Generate N fake products using Faker"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=500)

    def handle(self, *args, **options):
        with bypass_tenant():
            count = options["count"]

            tenant = Tenant.objects.first()
            if not tenant:
                self.stdout.write(self.style.ERROR("No tenant found. Run seed_data first."))
                return

            categories = list(Category.objects.filter(is_active=True))
            if not categories:
                self.stdout.write(self.style.ERROR("No categories found. Run seed_data first."))
                return

            units = list(Unit.objects.filter(is_active=True))
            if not units:
                self.stdout.write(self.style.ERROR("No units found. Run seed_data first."))
                return

            existing_skus = set(Product.objects.values_list("sku", flat=True))

            word_pool = [
                "Pro", "Max", "Ultra", "Lite", "Plus", "Premium", "Eco", "Smart",
                "Industrial", "Professional", "Portable", "Compact", "Heavy Duty",
                "Wireless", "Bluetooth", "USB", "Digital", "Ergonomic", "Solar",
                "Rechargeable", "Foldable", "Waterproof", "Stainless", "Optical",
                "High-Speed", "Multi", "Universal", "Adjustable", "Automatic",
            ]
            noun_pool = [
                "Scanner", "Printer", "Router", "Switch", "Hub", "Sensor", "Controller",
                "Dispenser", "Detector", "Regulator", "Converter", "Amplifier",
                "Processor", "Module", "Adapter", "Terminal", "Reader", "Display",
                "Panel", "Valve", "Pump", "Filter", "Compressor", "Generator",
                "Charger", "Cable", "Holder", "Bracket", "Mount", "Stand",
                "Organiser", "Cabinet", "Container", "Pallet", "Trolley", "Cart",
                "Lifter", "Sealer", "Wrapper", "Labeler", "Marker", "Tape",
            ]

            with transaction.atomic():
                created = 0
                for _ in range(count):
                    prefix = choice(["PRD", "TECH", "OFF", "IND", "STOR", "MACH", "TOOL", "SAFE", "CLEAN", "PACK"])
                    sku = f"{prefix}-{fake.unique.random_number(digits=5, fix_len=True)}"

                    if sku in existing_skus:
                        continue

                    name = f"{choice(word_pool)} {choice(noun_pool)}"
                    description = fake.sentence(nb_words=randint(6, 15))
                    category = choice(categories)
                    unit = choice(units)
                    cost_price = round(Decimal(str(uniform(5, 5000))), 2)

                    Product.objects.create(
                        sku=sku,
                        name=name,
                        description=description,
                        category=category,
                        unit=unit,
                        cost_price=cost_price,
                        is_active=choice([True, True, True, False]),
                        tenant=tenant,
                    )
                    existing_skus.add(sku)
                    created += 1

            self.stdout.write(self.style.SUCCESS(f"{created} fake products created."))
