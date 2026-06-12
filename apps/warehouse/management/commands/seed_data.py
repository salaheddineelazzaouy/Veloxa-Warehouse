from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.warehouse.models import Product, Location, StockMovement
from apps.backorder.models import BackOrder
from apps.crm.models import Customer
from apps.finance.models import Invoice, InvoiceLine
from apps.audit.models import AuditLog
from apps.landing.models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, SitePage

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample data for all models"

    def handle(self, *args, **options):
        self._seed_users()
        self._seed_locations()
        self._seed_products()
        self._seed_customers()
        self._seed_movements()
        self._seed_backorders()
        self._seed_invoices()
        self._seed_audit_logs()
        self._seed_landing()
        self.stdout.write(self.style.SUCCESS("Done. All models seeded."))

    def _seed_users(self):
        if User.objects.count() > 1:
            self.stdout.write("Users already exist, skipping.")
            return
        wm, _ = User.objects.get_or_create(
            username="manager", defaults={"email": "manager@veloxa.ma", "role": "warehouse_manager"},
        )
        wm.set_password("pass1234")
        wm.save()
        group = Group.objects.filter(name="warehouse_manager").first()
        if group:
            wm.groups.add(group)

        aud, _ = User.objects.get_or_create(
            username="auditor", defaults={"email": "auditor@veloxa.ma", "role": "auditor"},
        )
        aud.set_password("pass1234")
        aud.save()
        group = Group.objects.filter(name="auditor").first()
        if group:
            aud.groups.add(group)

        self.stdout.write(f"  Users: manager, auditor (password: pass1234)")

    def _seed_locations(self):
        codes = ["WH-A1", "WH-B2", "WH-C3", "COLD-1", "DRY-2"]
        for code in codes:
            Location.objects.get_or_create(code=code, defaults={"name": f"Location {code}"})
        self.stdout.write(f"  Locations: {len(codes)}")

    def _seed_products(self):
        if Product.objects.count() > 3:
            self.stdout.write("Products already exist, skipping.")
            return
        products = [
            ("ELEC-001", "Wireless Mouse", 45.00, "pcs"),
            ("ELEC-002", "Mechanical Keyboard", 120.00, "pcs"),
            ("ELEC-003", "USB-C Hub 7-in-1", 35.00, "pcs"),
            ("OFFICE-001", "A4 Paper Box (5 reams)", 25.00, "box"),
            ("OFFICE-002", "Stapler Heavy Duty", 15.00, "pcs"),
            ("STORAGE-001", "SSD 1TB NVMe", 89.00, "pcs"),
            ("STORAGE-002", "External HDD 4TB", 110.00, "pcs"),
            ("CONS-001", "AA Battery 12-pack", 12.00, "pack"),
            ("CONS-002", "HDMI Cable 2m", 8.00, "pcs"),
            ("FURN-001", "Standing Desk", 450.00, "unit"),
        ]
        for sku, name, price, unit in products:
            Product.objects.get_or_create(
                sku=sku,
                defaults={"name": name, "cost_price": price, "unit": unit},
            )
        self.stdout.write(f"  Products: {len(products)}")

    def _seed_customers(self):
        customers = [
            ("TechStore SARL", "+212661234567", "contact@techstore.ma", "Casablanca"),
            ("MegaCorp Afrique", "+212662345678", "info@megacorp.ma", "Rabat"),
            ("ShopOnline Maroc", "+212663456789", "sales@shoponline.ma", "Marrakech"),
        ]
        for name, phone, email, addr in customers:
            Customer.objects.get_or_create(
                name=name,
                defaults={"phone": phone, "email": email, "address": addr},
            )
        self.stdout.write(f"  Customers: {len(customers)}")

    def _seed_movements(self):
        if StockMovement.objects.count() > 5:
            self.stdout.write("Movements already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        products = Product.objects.all()[:5]
        loc = Location.objects.first()
        for i, product in enumerate(products):
            StockMovement.objects.create(
                product=product, qty=100 + i * 20,
                type=StockMovement.Type.INBOUND,
                reference=f"PO-SEED-{i+1:03d}",
                note="Seed data initial stock",
                location=loc, created_by=manager,
            )
            StockMovement.objects.create(
                product=product, qty=-(10 + i * 5),
                type=StockMovement.Type.OUTBOUND,
                reference=f"SO-SEED-{i+1:03d}",
                note="Seed data sale",
                location=loc, created_by=manager,
            )
        self.stdout.write(f"  Movements: {products.count() * 2}")

    def _seed_backorders(self):
        if BackOrder.objects.count() > 0:
            self.stdout.write("Backorders already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        product = Product.objects.filter(is_active=True).first()
        if product:
            BackOrder.objects.create(
                product=product, qty=15,
                sales_order_ref="SO-BO-001",
                created_by=manager,
            )
        self.stdout.write("  Backorders: 1")

    def _seed_invoices(self):
        if Invoice.objects.count() > 0:
            self.stdout.write("Invoices already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        if not manager:
            return
        products = Product.objects.all()[:3]
        customer = Customer.objects.first()
        invoice = Invoice.objects.create(
            invoice_ref="INV-SEED-001",
            order_ref="SO-SEED-001",
            customer=customer,
            total=0,  # will update
            created_by=manager,
        )
        total = 0
        for i, product in enumerate(products):
            line_total = (i + 1) * 10 * float(product.cost_price)
            InvoiceLine.objects.create(
                invoice=invoice, product=product,
                qty=(i + 1) * 10,
                unit_price=product.cost_price,
                total=line_total,
            )
            total += line_total
        invoice.total = total
        invoice.save(update_fields=["total"])
        self.stdout.write("  Invoices: 1")

    def _seed_audit_logs(self):
        if AuditLog.objects.count() > 0:
            self.stdout.write("Audit logs already exist, skipping.")
            return
        manager = User.objects.filter(role="warehouse_manager").first()
        AuditLog.objects.create(
            user=manager, action="create",
            table_name="warehouse_stockmovement",
            changes={"note": "Seed data import"},
        )
        self.stdout.write("  Audit logs: 1")

    def _seed_landing(self):
        if HeroSection.objects.exists():
            self.stdout.write("Landing content already exists, skipping.")
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
            ("Immutable stock ledger", "Every inbound, outbound, and adjustment is a permanent, signed movement. Current quantity is always derived via SUM() over the ledger — no stock field.", "fas fa-book", "#2563eb", "#1d4ed8", 0),
            ("Back-order isolation", "Deficit tracking runs in a separate bounded context. When inbound stock arrives, the system automatically fulfills open back-orders.", "fas fa-arrows-spin", "#7c3aed", "#6d28d9", 1),
            ("Audit trail + PII redaction", "Every mutation and PII read is logged. Raw PII never reaches log files — automatic redaction built in.", "fas fa-clipboard-list", "#059669", "#047857", 2),
            ("Role-based access", "Four built-in roles with granular permissions. Auditors can inspect every movement but never modify data.", "fas fa-users-cog", "#d97706", "#b45309", 3),
            ("Atomic transactions", "All stock operations run inside @transaction.atomic with row locking. No over-selling, no race conditions.", "fas fa-link", "#dc2626", "#b91c1c", 4),
            ("API-first", "Built with Django REST Framework + JWT. Rate limited at 100/h anonymous, 1,000/h authenticated. Full OpenAPI docs.", "fas fa-code", "#0d9488", "#0f766e", 5),
        ]
        for title, desc, icon, bg, bg_end, order in features_data:
            Feature.objects.create(title=title, description=desc, icon_class=icon, icon_bg=bg, icon_bg_end=bg_end, order=order)

        PricingPlan.objects.create(
            name="Starter", price="MAD 2,500", period="Up to 5 users · 10k movements/mo",
            features="Immutable ledger\nBasic audit trail\nEmail support (24h)\nJWT authentication",
            is_popular=False, button_text="Request demo", button_class="btn-outline", order=0,
        )
        PricingPlan.objects.create(
            name="Professional", price="MAD 6,900", period="Unlimited users · 100k movements/mo",
            features="Everything in Starter\nBack-order isolation + auto-fulfill\nFull audit trail + PII redaction\nPriority support (2h SLA)",
            is_popular=True, badge_text="Most popular", button_text="Request demo", button_class="btn-primary", order=1,
        )
        PricingPlan.objects.create(
            name="Enterprise", price="Custom", period="SLA 99.9% · On-prem or VPC",
            features="Everything in Professional\nDedicated success manager\nCustom compliance rules\nSSO / SAML + custom contracts",
            is_popular=False, button_text="Contact sales", button_class="btn-outline", order=2,
        )

        ComplianceSection.objects.create(
            title="Built for Moroccan compliance",
            law_title="Law 09-08 (CNDP)",
            items="<strong>Data minimisation</strong> — only collect name and phone number. No unnecessary PII stored.\n<strong>Right to anonymisation</strong> — after 5 years of inactivity, PII is irreversibly replaced with anonymous placeholders via a one-click service.\n<strong>Audit trail for PII access</strong> — every view of a customer record is logged with user ID and timestamp, including a dedicated <code>read_pii</code> action.\n<strong>Field-level encryption + TDE</strong> — phone and address are encrypted with AES-256-GCM at the column level, and the entire database is protected by Transparent Data Encryption at rest.",
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
            content="<h2>Our Mission</h2><p>Veloxa provides Moroccan businesses with an immutable, compliant inventory management system that eliminates stock discrepancies and ensures full auditability.</p><h2>Architecture</h2><p>Built as a modular monolith with Django 5.1, PostgreSQL 16, and Redis 7. Every stock movement is permanently recorded — there is no way to delete or alter a movement once created.</p><h2>Security</h2><p>All PII is encrypted at rest using AES-256-GCM field-level encryption. The database is protected by Transparent Data Encryption (TDE). All API traffic is secured with TLS 1.3 and JWT authentication with 30-minute token rotation.</p>",
        )
        SitePage.objects.create(
            slug="legal",
            title="Legal & Compliance",
            content="<h2>Terms of Service</h2><p>Veloxa Warehouse is provided as a SaaS platform. By using our service, you agree to our terms and conditions.</p><h2>Data Protection</h2><p>We comply with Moroccan Law 09-08 (CNDP) regarding the protection of personal data. All customer PII is encrypted at rest using AES-256-GCM. We maintain a full audit trail of all data access.</p><h2>Privacy Policy</h2><p>We collect only the data necessary to provide our service: name, email, phone, and address. Data is retained for the duration of the service agreement plus 5 years, after which PII is anonymized.</p><h2>SLA</h2><p>Enterprise customers receive 99.9% uptime SLA. Support response times: Enterprise 1h, Professional 2h, Starter 24h.</p>",
        )

        self.stdout.write("  Landing content: seeded")
