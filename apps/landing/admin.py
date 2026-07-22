from django.contrib import admin
from .models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage
from ckeditor.widgets import CKEditorWidget
from django import forms

class SitePageAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name="default"))
    class Meta:
        model = SitePage
        fields = "__all__"

class SitePageAdmin(admin.ModelAdmin):
    form = SitePageAdminForm

admin.site.register(HeroSection)
admin.site.register(Feature)
admin.site.register(TrustCard)
admin.site.register(PricingPlan)
admin.site.register(ComplianceSection)
admin.site.register(CTASection)
admin.site.register(LandingLead)
admin.site.register(SitePage, SitePageAdmin)
