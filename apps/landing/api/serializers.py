from rest_framework import serializers
from ..models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = "__all__"


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"


class TrustCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustCard
        fields = "__all__"


class PricingPlanSerializer(serializers.ModelSerializer):
    feature_list = serializers.ReadOnlyField()

    class Meta:
        model = PricingPlan
        fields = "__all__"


class ComplianceSectionSerializer(serializers.ModelSerializer):
    item_list = serializers.ReadOnlyField()

    class Meta:
        model = ComplianceSection
        fields = "__all__"


class CTASectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CTASection
        fields = "__all__"


class LandingLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingLead
        fields = "__all__"
        read_only_fields = ["created_at"]


class SitePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SitePage
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
