from django.db import models


class HeroSection(models.Model):
    headline = models.CharField(max_length=255, default="Inventory you can trust. Stock you can verify.")
    subtitle = models.TextField(default="Immutable ledger, automated back-orders, and full audit trails...")
    cta_text = models.CharField(max_length=100, default="Start free trial")
    cta_link = models.CharField(max_length=255, default="#contact")
    secondary_cta_text = models.CharField(max_length=100, default="Read the architecture")
    secondary_cta_link = models.CharField(max_length=255, default="#architecture")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_hero"
        verbose_name = "Hero Section"

    def __str__(self):
        return self.headline[:60]


class Feature(models.Model):
    icon_bg = models.CharField(max_length=7, default="#2563eb", help_text="CSS gradient start")
    icon_bg_end = models.CharField(max_length=7, default="#1d4ed8", help_text="CSS gradient end")
    icon_class = models.CharField(max_length=100, default="fas fa-book", help_text="FontAwesome icon class")
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_feature"
        ordering = ["order"]
        verbose_name = "Feature"

    def __str__(self):
        return self.title


class TrustCard(models.Model):
    icon_bg = models.CharField(max_length=100, default="linear-gradient(135deg,#2563eb,#1d4ed8)")
    icon_class = models.CharField(max_length=100, default="fas fa-shield-alt")
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_trust_card"
        ordering = ["order"]
        verbose_name = "Trust Card"

    def __str__(self):
        return self.title


class PricingPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.CharField(max_length=100, help_text="e.g. MAD 2,500 or 'Custom'")
    period = models.CharField(max_length=200, help_text="e.g. 'Up to 5 users · 10k movements/mo'")
    features = models.TextField(help_text="One feature per line")
    is_popular = models.BooleanField(default=False)
    badge_text = models.CharField(max_length=100, blank=True, default="Most popular")
    button_text = models.CharField(max_length=100, default="Request demo")
    button_class = models.CharField(max_length=50, default="btn-outline", help_text="btn-primary, btn-outline, etc.")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_pricing_plan"
        ordering = ["order"]
        verbose_name = "Pricing Plan"

    def __str__(self):
        return self.name

    def feature_list(self):
        return [f.strip() for f in self.features.split("\n") if f.strip()]


class ComplianceSection(models.Model):
    title = models.CharField(max_length=255, default="Built for Moroccan compliance")
    law_title = models.CharField(max_length=255, default="Law 09-08 (CNDP)")
    items = models.TextField(help_text="One compliance item per line")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_compliance"
        verbose_name = "Compliance Section"

    def __str__(self):
        return self.title

    def item_list(self):
        return [i.strip() for i in self.items.split("\n") if i.strip()]


class CTASection(models.Model):
    headline = models.CharField(max_length=255, default="Ready to move beyond spreadsheets?")
    subtitle = models.CharField(max_length=255, default="Join Moroccan logistics teams that trust Veloxa.")
    button_text = models.CharField(max_length=100, default="Get early access")
    placeholder = models.CharField(max_length=255, default="Enter your work email")
    footnote = models.CharField(max_length=255, default="No credit card required. 14-day free trial.")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "landing_cta"
        verbose_name = "CTA Section"

    def __str__(self):
        return self.headline[:60]


class LandingLead(models.Model):
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "landing_lead"
        ordering = ["-created_at"]
        verbose_name = "Landing Lead"

    def __str__(self):
        return self.email


class SitePage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="HTML content")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "landing_site_page"
        verbose_name = "Site Page"
        verbose_name_plural = "Site Pages"

    def __str__(self):
        return self.title
