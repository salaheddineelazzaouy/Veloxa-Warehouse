import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from random import randint, uniform, choice, sample
from faker import Faker
from apps.warehouse.models import Product, Location, StockMovement, Category, Unit
from apps.tenants.models import Tenant
from apps.backorder.models import BackOrder
from apps.crm.models import Customer
from apps.finance.models import Invoice, InvoiceLine
from apps.audit.models import AuditLog
from apps.landing.models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, SitePage
from apps.subscriptions.models import SubscriptionPlan, Subscription, PaymentTransaction

logging.getLogger("faker").setLevel(logging.WARNING)

User = get_user_model()
fake = Faker(["fr_FR"])


class Command(BaseCommand):
    help = "Seed the database with realistic fake data"

    def handle(self, *args, **options):
        self._seed_tenants()
        self._seed_users()
        self._seed_locations()
        self._seed_categories()
        self._seed_units()
        self._seed_products()
        self._seed_customers()
        self._seed_movements()
        self._seed_backorders()
        self._seed_invoices()
        self._seed_audit_logs()
        self._seed_landing()
        self._seed_subscriptions()
        self.stdout.write(self.style.SUCCESS("Done. All models seeded."))

    def _seed_tenants(self):
        tenant, _ = Tenant.objects.get_or_create(
            slug="default", defaults={"name": "Default Tenant"},
        )
        self.default_tenant = tenant

    def _seed_users(self):
        if User.objects.count() > 1:
            self.stdout.write("  Users already exist, skipping.")
            return
        roles = [
            ("manager", "warehouse_manager", "manager@veloxa.ma"),
            ("auditor", "auditor", "auditor@veloxa.ma"),
            ("operator", "warehouse_manager", "operator@veloxa.ma"),
            ("viewer", "viewer", "viewer@veloxa.ma"),
        ]
        for username, role, email in roles:
            user, _ = User.objects.get_or_create(
                username=username, defaults={"email": email, "role": role, "tenant": self.default_tenant},
            )
            user.set_password("pass1234")
            user.save()
            group = Group.objects.filter(name=role).first()
            if group:
                user.groups.add(group)
        self.stdout.write("  Users: manager, auditor, operator, viewer (password: pass1234)")

    def _seed_locations(self):
        if Location.objects.count() > 3:
            self.stdout.write("  Locations already exist, skipping.")
            return
        prefixes = ["WH", "COLD", "DRY", "HAZ", "PICK"]
        for prefix in prefixes:
            for num in range(1, 4):
                code = f"{prefix}-{chr(64+num)}{num}"
                Location.objects.get_or_create(
                    code=code,
                    defaults={"name": f"{dict(zip(prefixes, ['Warehouse', 'Cold Storage', 'Dry Storage', 'Hazardous', 'Picking Zone'])).get(prefix, 'Area')} {num}", "is_active": True, "tenant": self.default_tenant},
                )
        self.stdout.write(f"  Locations: {Location.objects.count()}")

    def _seed_categories(self):
        if Category.objects.count() > 3:
            self.stdout.write("  Categories already exist, skipping.")
            return
        names = [
            "Electronics", "Office Supplies", "Storage & Memory",
            "Consumables", "Furniture", "Networking", "Cables & Adaptors",
            "Cleaning Supplies", "Packaging", "Safety Equipment",
        ]
        for name in names:
            Category.objects.get_or_create(
                name=name,
                defaults={"description": fake.catch_phrase(), "is_active": True, "tenant": self.default_tenant},
            )
        self.stdout.write(f"  Categories: {len(names)}")

    def _seed_units(self):
        if Unit.objects.count() > 3:
            self.stdout.write("  Units already exist, skipping.")
            return
        units = [
            ("Piece", "pcs"), ("Box", "box"), ("Pack", "pack"),
            ("Unit", "unit"), ("Kilogram", "kg"), ("Meter", "m"),
            ("Liter", "l"), ("Set", "set"), ("Pair", "pair"),
            ("Carton", "ctn"), ("Roll", "rl"), ("Bottle", "btl"),
        ]
        for name, abbr in units:
            Unit.objects.get_or_create(name=name, defaults={"abbreviation": abbr, "is_active": True})
        self.stdout.write(f"  Units: {len(units)}")

    def _seed_products(self):
        if Product.objects.count() > 3:
            self.stdout.write("  Products already exist, skipping.")
            return
        categories = list(Category.objects.filter(is_active=True))
        units = list(Unit.objects.filter(is_active=True))
        product_defs = [
            ("ELEC", "Wireless Mouse", 120.0, 450.0),
            ("ELEC", "Mechanical Keyboard", 250.0, 1200.0),
            ("ELEC", "USB-C Hub 7-in-1", 80.0, 350.0),
            ("ELEC", "27\" Monitor", 1800.0, 5500.0),
            ("ELEC", "Webcam 1080p", 200.0, 600.0),
            ("ELEC", "Bluetooth Speaker", 150.0, 800.0),
            ("ELEC", "Noise-Cancelling Headphones", 400.0, 2500.0),
            ("OFFICE", "A4 Paper Box (5 reams)", 60.0, 250.0),
            ("OFFICE", "Stapler Heavy Duty", 30.0, 150.0),
            ("OFFICE", "Desk Organiser", 45.0, 200.0),
            ("OFFICE", "Whiteboard 90x120cm", 120.0, 450.0),
            ("OFFICE", "Paper Shredder", 350.0, 900.0),
            ("OFFICE", "Binding Machine", 500.0, 1400.0),
            ("STORAGE", "SSD 1TB NVMe", 400.0, 890.0),
            ("STORAGE", "External HDD 4TB", 500.0, 1100.0),
            ("STORAGE", "USB Flash Drive 128GB", 50.0, 180.0),
            ("STORAGE", "NAS 2-Bay", 1200.0, 3500.0),
            ("STORAGE", "SD Card 256GB", 100.0, 350.0),
            ("STORAGE", "Portable SSD 500GB", 350.0, 950.0),
            ("CONS", "AA Battery 12-pack", 20.0, 120.0),
            ("CONS", "HDMI Cable 2m", 15.0, 80.0),
            ("CONS", "USB-C Cable 1m", 12.0, 60.0),
            ("CONS", "Ethernet Cable 5m", 25.0, 90.0),
            ("CONS", "Power Strip 6-outlet", 80.0, 250.0),
            ("CONS", "AA Rechargeable Batteries 4-pack", 40.0, 160.0),
            ("FURN", "Standing Desk", 2000.0, 4500.0),
            ("FURN", "Ergonomic Office Chair", 1500.0, 3800.0),
            ("FURN", "Monitor Arm Dual", 250.0, 800.0),
            ("FURN", "Bookshelf 3-tier", 400.0, 1200.0),
            ("FURN", "Filing Cabinet", 600.0, 1800.0),
            ("NET", "WiFi 6 Router", 300.0, 1200.0),
            ("NET", "Network Switch 24-port", 800.0, 2800.0),
            ("NET", "Access Point", 400.0, 1500.0),
            ("NET", "Patch Panel 24-port", 200.0, 700.0),
            ("CABLE", "DisplayPort 1.4 Cable 2m", 30.0, 120.0),
            ("CABLE", "VGA Cable 1.8m", 15.0, 55.0),
            ("CABLE", "3.5mm Audio Cable", 10.0, 40.0),
            ("CABLE", "RCA Cable 2m", 12.0, 45.0),
        ]
        products = []
        for i, (prefix, name, min_price, max_price) in enumerate(product_defs, 1):
            cat = choice(categories)
            unit = choice(units)
            price = round(uniform(min_price, max_price) / 10) * 10 / 100
            price = round(Decimal(str(price)), 2)
            products.append((f"{prefix}-{i:03d}", name, price, cat, unit))
        for sku, name, price, cat, unit in products:
            Product.objects.get_or_create(
                sku=sku,
                defaults={"name": name, "cost_price": price, "category": cat, "unit": unit, "description": fake.sentence(), "is_active": True, "tenant": self.default_tenant},
            )
        self.stdout.write(f"  Products: {len(products)}")

    def _seed_customers(self):
        cities = [
            "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir",
            "Meknès", "Oujda", "Kenitra", "Tétouan", "Safi", "El Jadida",
            "Mohammedia", "Laâyoune", "Khouribga", "Béni Mellal",
        ]
        company_suffixes = [
            "S.A.R.L.", "S.A.S.", "S.A.", "SARL", "& Fils", "& Associés",
            "S.N.C.", "E.U.R.L.",
        ]
        industries = [
            "Logistique", "Informatique", "BTP", "Agroalimentaire", "Textile",
            "Automobile", "Pharmaceutique", "Électronique", "Métallurgie",
            "Chimie", "Distribution", "Transport", "Énergie",
        ]

        def generate_customer_data():
            company = fake.company()
            if randint(0, 1):
                company = f"{company} {choice(company_suffixes)}"

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
            city = choice(cities)
            zip_code = f"{randint(10000, 99999)}"
            address = choice([
                f"{street_num}, {street}, {city}",
                f"{street_num}, {street}, {zip_code} {city}",
                f"Angle {fake.street_name()} et {fake.street_name()}, {city}",
                f"Quartier {fake.word().capitalize()}, {street_num} {street}, {city}",
                f"Résidence {fake.last_name()}, {street_num} {street}, {city}",
            ])

            identifiant_fiscal = f"{randint(100000, 999999)}"
            taxe_professionnelle = f"TP-{randint(1000, 9999)}/{choice(cities)[:3].upper()}"
            registre_commerce = f"{randint(10000, 99999)}/{choice(['Casablanca', 'Rabat', 'Marrakech'])}"

            metadata = {
                "industry": choice(industries),
                "notes": fake.sentence(),
                "contact_person": f"{fake.first_name()} {fake.last_name()}",
                "since": fake.date_between(start_date="-5y", end_date="today").isoformat(),
            }
            return company, ice, identifiant_fiscal, taxe_professionnelle, registre_commerce, phone, email, address, metadata

        existing = list(Customer.objects.filter(tenant=self.default_tenant))
        if existing:
            for c in existing:
                _, ice, if_, tp, rc, phone, email, address, metadata = generate_customer_data()
                c.ice = ice
                c.identifiant_fiscal = if_
                c.taxe_professionnelle = tp
                c.registre_commerce = rc
                c.phone = phone
                c.email = email
                c.address = address
                c.metadata = metadata
            Customer.objects.bulk_update(existing, ["ice", "identifiant_fiscal",
                                                     "taxe_professionnelle", "registre_commerce",
                                                     "phone", "email", "address", "metadata"])
            self.stdout.write(f"  Customers: {len(existing)} updated")
        else:
            customers = []
            for _ in range(25):
                name, ice, if_, tp, rc, phone, email, address, metadata = generate_customer_data()
                customers.append(Customer(
                    name=name, ice=ice,
                    identifiant_fiscal=if_, taxe_professionnelle=tp,
                    registre_commerce=rc,
                    phone=phone, email=email, address=address,
                    metadata=metadata,
                    is_active=True, tenant=self.default_tenant,
                ))
            Customer.objects.bulk_create(customers)
            self.stdout.write(f"  Customers: {len(customers)} created")

    def _seed_movements(self):
        if StockMovement.objects.count() > 5:
            self.stdout.write("  Movements already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        products = list(Product.objects.filter(is_active=True))
        locations = list(Location.objects.filter(is_active=True))
        with transaction.atomic():
            for i, product in enumerate(products):
                inbound_qty = randint(50, 500)
                loc = choice(locations)
                StockMovement.objects.create(
                    product=product, qty=inbound_qty,
                    type=StockMovement.Type.INBOUND,
                    reference=f"PO-{fake.date_this_year().strftime('%Y%m%d')}-{i+1:03d}",
                    note=f"Purchase order from {fake.company()}",
                    location=loc, created_by=manager,
                    tenant=self.default_tenant,
                )
                if randint(0, 1):
                    outbound_qty = randint(5, min(50, inbound_qty // 2))
                    StockMovement.objects.create(
                        product=product, qty=-outbound_qty,
                        type=StockMovement.Type.OUTBOUND,
                        reference=f"SO-{fake.date_this_year().strftime('%Y%m%d')}-{i+1:03d}",
                        note=f"Sales order — {fake.company()}",
                        location=loc, created_by=manager,
                        tenant=self.default_tenant,
                    )
                if randint(0, 3) == 0:
                    adj_qty = randint(-20, 20)
                    if adj_qty != 0:
                        StockMovement.objects.create(
                            product=product, qty=adj_qty,
                            type=StockMovement.Type.ADJUSTMENT,
                            reference=f"ADJ-{fake.date_this_year().strftime('%Y%m%d')}-{i+1:03d}",
                            note=f"Cycle count adjustment: {fake.word()}",
                            location=loc, created_by=manager,
                            tenant=self.default_tenant,
                        )
        count = StockMovement.objects.count()
        self.stdout.write(f"  Movements: {count}")

    def _seed_backorders(self):
        if BackOrder.objects.count() > 0:
            self.stdout.write("  Backorders already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        products = list(Product.objects.filter(is_active=True))
        with transaction.atomic():
            for _ in range(randint(3, 6)):
                product = choice(products)
                BackOrder.objects.create(
                    product=product,
                    qty=randint(5, 50),
                    sales_order_ref=f"SO-BO-{fake.date_this_year().strftime('%Y%m%d')}-{randint(100,999)}",
                    created_by=manager,
                    tenant=self.default_tenant,
                )
        count = BackOrder.objects.count()
        self.stdout.write(f"  Backorders: {count}")

    def _seed_invoices(self):
        if Invoice.objects.count() > 0:
            self.stdout.write("  Invoices already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        products = list(Product.objects.filter(is_active=True))
        customers = list(Customer.objects.all())
        with transaction.atomic():
            for i in range(randint(3, 6)):
                customer = choice(customers) if customers else None
                order_ref = f"SO-{fake.date_this_year().strftime('%Y%m%d')}-{i+1:03d}"
                invoice = Invoice.objects.create(
                    invoice_ref=f"INV-{order_ref}",
                    order_ref=order_ref,
                    customer=customer,
                    total=Decimal("0"),
                    created_by=manager,
                    tenant=self.default_tenant,
                )
                total = Decimal("0")
                line_products = sample(products, min(randint(1, 4), len(products)))
                for j, product in enumerate(line_products):
                    qty = randint(1, 20)
                    unit_price = product.cost_price * Decimal(str(uniform(1.1, 1.4))).quantize(Decimal("0.01"))
                    line_total = Decimal(str(qty)) * unit_price
                    InvoiceLine.objects.create(
                        invoice=invoice, product=product,
                        qty=qty, unit_price=unit_price, total=line_total,
                        tenant=self.default_tenant,
                    )
                    total += line_total
                invoice.total = total.quantize(Decimal("0.01"))
                invoice.save(update_fields=["total"])
        count = Invoice.objects.count()
        self.stdout.write(f"  Invoices: {count}")

    def _seed_audit_logs(self):
        if AuditLog.objects.count() > 0:
            self.stdout.write("  Audit logs already exist, skipping.")
            return
        users = list(User.objects.all())
        actions = ["create", "update", "read_pii", "delete"]
        tables = [
            "warehouse_product", "warehouse_stockmovement",
            "crm_customer", "finance_invoice", "backorder_backorder",
        ]
        with transaction.atomic():
            for _ in range(20):
                AuditLog.objects.create(
                    user=choice(users),
                    action=choice(actions),
                    table_name=choice(tables),
                    changes={"note": fake.sentence(), "timestamp": fake.iso8601()},
                    tenant=self.default_tenant,
                )
        count = AuditLog.objects.count()
        self.stdout.write(f"  Audit logs: {count}")

    def _seed_landing(self):
        if HeroSection.objects.exists():
            self.stdout.write("  Landing content already exists, skipping.")
            return

        HeroSection.objects.create(
            headline="Inventory you can trust. Stock you can verify.",
            subtitle="Immutable ledger, automated back-orders, and full audit trails — all in a modular monolith. Compliant with CNDP/PCM and built for Moroccan logistics.",
            cta_text="Start free trial",
            cta_link="/contact/",
            secondary_cta_text="Read the architecture",
            secondary_cta_link="/about/",
        )

        TrustCard.objects.create(
            icon_bg="linear-gradient(135deg,#2563eb,#1d4ed8)", icon_class="fas fa-shield-alt",
            title="AES-256-GCM encryption",
            description="Phone numbers and addresses are encrypted at the field level using AES-256-GCM. Database TDE adds a second layer of protection at rest.",
            order=0,
        )
        TrustCard.objects.create(
            icon_bg="linear-gradient(135deg,#7c3aed,#6d28d9)", icon_class="fas fa-key",
            title="RBAC + JWT",
            description="Granular roles (Warehouse Manager, Auditor, Read-Only) enforced through signed JWTs with 30-minute token rotation and refresh.",
            order=1,
        )
        TrustCard.objects.create(
            icon_bg="linear-gradient(135deg,#059669,#047857)", icon_class="fas fa-check-circle",
            title="GDPR / CNDP ready",
            description="Built to comply with Moroccan Law 09-08. Data minimisation, right to anonymisation, and full audit trail for every PII access.",
            order=2,
        )

        features_data = [
            ("Immutable stock ledger", "Every inbound, outbound, and adjustment is a permanent, signed movement. Current quantity is always derived via SUM() over the ledger \u2014 no stock field.", "fas fa-book", "#2563eb", "#1d4ed8", 0),
            ("Back-order isolation", "Deficit tracking runs in a separate bounded context. When inbound stock arrives, the system automatically fulfills open back-orders.", "fas fa-arrows-spin", "#7c3aed", "#6d28d9", 1),
            ("Audit trail + PII redaction", "Every mutation and PII read is logged. Raw PII never reaches log files \u2014 automatic redaction built in.", "fas fa-clipboard-list", "#059669", "#047857", 2),
            ("Role-based access", "Four built-in roles with granular permissions. Auditors can inspect every movement but never modify data.", "fas fa-users-cog", "#d97706", "#b45309", 3),
            ("Atomic transactions", "All stock operations run inside @transaction.atomic with row locking. No over-selling, no race conditions.", "fas fa-link", "#dc2626", "#b91c1c", 4),
            ("API-first", "Built with Django REST Framework + JWT. Rate limited at 100/h anonymous, 1,000/h authenticated. Full OpenAPI docs.", "fas fa-code", "#0d9488", "#0f766e", 5),
        ]
        for title, desc, icon, bg, bg_end, order in features_data:
            Feature.objects.create(title=title, description=desc, icon_class=icon, icon_bg=bg, icon_bg_end=bg_end, order=order)

        PricingPlan.objects.create(
            name="Starter", price="MAD 2,500", period="Up to 5 users \u00b7 10k movements/mo",
            features="Immutable ledger\nBasic audit trail\nEmail support (24h)\nJWT authentication",
            is_popular=False, button_text="Request demo", button_class="btn-outline", order=0,
        )
        PricingPlan.objects.create(
            name="Professional", price="MAD 6,900", period="Unlimited users \u00b7 100k movements/mo",
            features="Everything in Starter\nBack-order isolation + auto-fulfill\nFull audit trail + PII redaction\nPriority support (2h SLA)",
            is_popular=True, badge_text="Most popular", button_text="Request demo", button_class="btn-primary", order=1,
        )
        PricingPlan.objects.create(
            name="Enterprise", price="Custom", period="SLA 99.9% \u00b7 On-prem or VPC",
            features="Everything in Professional\nDedicated success manager\nCustom compliance rules\nSSO / SAML + custom contracts",
            is_popular=False, button_text="Contact sales", button_class="btn-outline", order=2,
        )

        ComplianceSection.objects.create(
            title="Built for Moroccan compliance",
            law_title="Law 09-08 (CNDP)",
            items="<strong>Data minimisation</strong> \u2014 only collect name and phone number. No unnecessary PII stored.\n<strong>Right to anonymisation</strong> \u2014 after 5 years of inactivity, PII is irreversibly replaced with anonymous placeholders via a one-click service.\n<strong>Audit trail for PII access</strong> \u2014 every view of a customer record is logged with user ID and timestamp, including a dedicated <code>read_pii</code> action.\n<strong>Field-level encryption + TDE</strong> \u2014 phone and address are encrypted with AES-256-GCM at the column level, and the entire database is protected by Transparent Data Encryption at rest.",
        )

        CTASection.objects.create(
            headline="Ready to move beyond spreadsheets?",
            subtitle="Join Moroccan logistics teams that trust Veloxa for their warehouse data.",
            button_text="Get early access",
            placeholder="Enter your work email",
            footnote="No credit card required. 14-day free trial.",
        )

        SitePage.objects.create(
            slug="about",
            title="About Veloxa Warehouse",
            content="<h2>Our Mission</h2><p>Veloxa provides Moroccan businesses with an immutable, compliant inventory management system that eliminates stock discrepancies and ensures full auditability.</p><h2>Architecture</h2><p>Built as a modular monolith with Django 5.1, PostgreSQL 16, and Redis 7. Every stock movement is permanently recorded \u2014 there is no way to delete or alter a movement once created.</p><h2>Security</h2><p>All PII is encrypted at rest using AES-256-GCM field-level encryption. The database is protected by Transparent Data Encryption (TDE). All API traffic is secured with TLS 1.3 and JWT authentication with 30-minute token rotation.</p>",
        )
        SitePage.objects.create(
            slug="legal",
            title="Legal & Compliance",
            content="<h2>Terms of Service</h2><p>Veloxa Warehouse is provided as a SaaS platform. By using our service, you agree to our terms and conditions.</p><h2>Data Protection</h2><p>We comply with Moroccan Law 09-08 (CNDP) regarding the protection of personal data. All customer PII is encrypted at rest using AES-256-GCM. We maintain a full audit trail of all data access.</p><h2>Privacy Policy</h2><p>We collect only the data necessary to provide our service: name, email, phone, and address. Data is retained for the duration of the service agreement plus 5 years, after which PII is anonymized.</p><h2>SLA</h2><p>Enterprise customers receive 99.9% uptime SLA. Support response times: Enterprise 1h, Professional 2h, Starter 24h.</p>",
        )

        self.stdout.write("  Landing content: seeded")

    def _seed_subscriptions(self):
        if SubscriptionPlan.objects.count() > 0:
            self.stdout.write("  Subscriptions already exist, skipping.")
            return

        now = timezone.now()

        plans_data = [
            {
                "name": "Starter",
                "description": "Essential inventory tracking for small teams",
                "price_monthly": Decimal("2500.00"),
                "price_yearly": Decimal("25000.00"),
                "features": {
                    "max_products": 100,
                    "max_users": 5,
                    "max_stock_movements_per_month": 10000,
                    "backorder_tracking": False,
                    "audit_log_retention_days": 30,
                    "api_rate_limit_per_hour": 100,
                    "support_sla_hours": 24,
                },
            },
            {
                "name": "Professional",
                "description": "Full features for growing logistics operations",
                "price_monthly": Decimal("6900.00"),
                "price_yearly": Decimal("69000.00"),
                "features": {
                    "max_products": 5000,
                    "max_users": 25,
                    "max_stock_movements_per_month": 100000,
                    "backorder_tracking": True,
                    "audit_log_retention_days": 365,
                    "api_rate_limit_per_hour": 1000,
                    "support_sla_hours": 2,
                },
            },
            {
                "name": "Enterprise",
                "description": "Custom deployment with dedicated support",
                "price_monthly": Decimal("0.00"),
                "price_yearly": Decimal("0.00"),
                "features": {
                    "max_products": 0,
                    "max_users": 0,
                    "max_stock_movements_per_month": 0,
                    "backorder_tracking": True,
                    "audit_log_retention_days": 1095,
                    "api_rate_limit_per_hour": 10000,
                    "support_sla_hours": 1,
                },
            },
        ]

        with transaction.atomic():
            plans = []
            for data in plans_data:
                plan, _ = SubscriptionPlan.objects.get_or_create(
                    name=data["name"],
                    defaults=data,
                )
                plans.append(plan)
        self.stdout.write(f"  Subscription plans: {len(plans)}")

        users = list(User.objects.exclude(role="viewer"))
        if not users:
            self.stdout.write("  No users to assign subscriptions to.")
            return
        elif Subscription.objects.count() > 0:
            self.stdout.write("  Subscriptions already exist, skipping.")
            return

        with transaction.atomic():
            for user in users:
                plan = choice(plans)
                status = choice(["active", "active", "active", "pending_payment"])
                start = now - timedelta(days=randint(1, 90))
                end = start + timedelta(days=365 if status == "active" else 0)
                sub = Subscription.objects.create(
                    user=user,
                    plan=plan if plan.price_monthly else plans[0],
                    status=status,
                    start_date=start,
                    end_date=end if status == "active" else None,
                    billing_cycle=choice(["monthly", "monthly", "yearly"]),
                    last_payment_date=start,
                    next_payment_date=start + timedelta(days=30),
                    tenant=self.default_tenant,
                )
                if status == "active":
                    PaymentTransaction.objects.create(
                        user=user,
                        subscription=sub,
                        amount=plan.price_monthly or Decimal("2500.00"),
                        currency="MAD",
                        payment_method=choice(["bank_transfer", "bank_transfer", "cih"]),
                        reference_number=f"PAY-{user.id}-{fake.date_this_year().strftime('%Y%m%d')}-{randint(1000,9999)}",
                        status="verified",
                        verified_by=choice(users),
                        verified_at=start,
                        plan=plan,
                        billing_cycle=sub.billing_cycle,
                        tenant=self.default_tenant,
                    )
        subs_count = Subscription.objects.count()
        payments_count = PaymentTransaction.objects.count()
        self.stdout.write(f"  Subscriptions: {subs_count}")
        self.stdout.write(f"  Payment transactions: {payments_count}")
