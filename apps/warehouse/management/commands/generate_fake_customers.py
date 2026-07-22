import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from random import randint, choice
from faker import Faker
from apps.crm.models import Customer
from apps.tenants.models import Tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])

CITIES = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir",
    "Meknès", "Oujda", "Kenitra", "Tétouan", "Safi", "El Jadida",
    "Mohammedia", "Laâyoune", "Khouribga", "Béni Mellal",
]
COMPANY_SUFFIXES = ["S.A.R.L.", "S.A.S.", "S.A.", "SARL", "& Fils", "& Associés", "S.N.C.", "E.U.R.L."]
INDUSTRIES = [
    "Logistique", "Informatique", "BTP", "Agroalimentaire", "Textile",
    "Automobile", "Pharmaceutique", "Électronique", "Métallurgie",
    "Chimie", "Distribution", "Transport", "Énergie",
]


def generate_customer_data():
    company = fake.company()
    if randint(0, 1):
        company = f"{company} {choice(COMPANY_SUFFIXES)}"

    ice = f"{randint(100000000000000, 999999999999999)}"
    phone = f"+2126{randint(10000000, 99999999)}"

    domain = fake.domain_name()
    email_parts = company.lower().replace(" ", "").replace("-", "").replace("'", "")[:12]
    email_parts = email_parts.rstrip(". -_")
    email = choice([
        f"contact@{email_parts}.{domain.split('.')[-1]}",
        f"info@{email_parts}.{domain.split('.')[-1]}",
        f"{fake.first_name().lower()}.{fake.last_name().lower()}@{email_parts}.{domain.split('.')[-1]}",
    ])

    street_num = randint(1, 500)
    street = fake.street_name()
    city = choice(CITIES)
    zip_code = f"{randint(10000, 99999)}"
    address = choice([
        f"{street_num}, {street}, {city}",
        f"{street_num}, {street}, {zip_code} {city}",
        f"Angle {fake.street_name()} et {fake.street_name()}, {city}",
        f"Quartier {fake.word().capitalize()}, {street_num} {street}, {city}",
        f"Résidence {fake.last_name()}, {street_num} {street}, {city}",
    ])

    identifiant_fiscal = f"{randint(100000, 999999)}"
    taxe_professionnelle = f"TP-{randint(1000, 9999)}/{choice(CITIES)[:3].upper()}"
    registre_commerce = f"{randint(10000, 99999)}/{choice(['Casablanca', 'Rabat', 'Marrakech'])}"

    metadata = {
        "industry": choice(INDUSTRIES),
        "notes": fake.sentence(),
        "contact_person": f"{fake.first_name()} {fake.last_name()}",
        "since": fake.date_between(start_date="-5y", end_date="today").isoformat(),
    }
    return company, ice, identifiant_fiscal, taxe_professionnelle, registre_commerce, phone, email, address, metadata


class Command(BaseCommand):
    help = "Generate N fake customers using Faker"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=250)

    def handle(self, *args, **options):
        count = options["count"]

        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR("No tenant found. Run seed_data first."))
            return

        existing_names = set(Customer.objects.filter(tenant=tenant).values_list("name", flat=True))

        with transaction.atomic():
            created = 0
            attempts = 0
            while created < count and attempts < count * 3:
                name, ice, if_, tp, rc, phone, email, address, metadata = generate_customer_data()
                attempts += 1
                if name in existing_names:
                    continue
                Customer.objects.create(
                    name=name, ice=ice,
                    identifiant_fiscal=if_, taxe_professionnelle=tp,
                    registre_commerce=rc,
                    phone=phone, email=email, address=address,
                    metadata=metadata,
                    is_active=True, tenant=tenant,
                )
                existing_names.add(name)
                created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} fake customers created."))
