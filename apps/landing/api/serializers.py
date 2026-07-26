from rest_framework import serializers
from ..models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ["id", "headline", "subtitle", "cta_text", "cta_link", "secondary_cta_text", "secondary_cta_link", "is_active"]


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "icon_bg", "icon_bg_end", "icon_class", "title", "description", "order", "is_active"]


class TrustCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustCard
        fields = ["id", "icon_bg", "icon_class", "title", "description", "order", "is_active"]


class PricingPlanSerializer(serializers.ModelSerializer):
    feature_list = serializers.ReadOnlyField()

    class Meta:
        model = PricingPlan
        fields = ["id", "name", "price", "period", "features", "feature_list", "is_popular", "badge_text", "button_text", "button_class", "order", "is_active"]


class ComplianceSectionSerializer(serializers.ModelSerializer):
    item_list = serializers.ReadOnlyField()

    class Meta:
        model = ComplianceSection
        fields = ["id", "title", "law_title", "items", "item_list", "is_active"]


class CTASectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CTASection
        fields = ["id", "headline", "subtitle", "button_text", "placeholder", "footnote", "is_active"]


class LandingLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingLead
        fields = ["id", "name", "email", "company", "message", "created_at"]
        read_only_fields = ["created_at"]


class SitePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SitePage
        fields = ["id", "slug", "title", "content", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
