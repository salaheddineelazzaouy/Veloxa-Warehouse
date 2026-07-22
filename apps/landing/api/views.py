from rest_framework import viewsets, permissions, mixins
from ..models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage
from .serializers import (
    HeroSectionSerializer, FeatureSerializer, TrustCardSerializer,
    PricingPlanSerializer, ComplianceSectionSerializer, CTASectionSerializer,
    LandingLeadSerializer, SitePageSerializer,
)


class HeroSectionViewSet(viewsets.ModelViewSet):
    queryset = HeroSection.objects.filter(is_active=True)
    serializer_class = HeroSectionSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.filter(is_active=True)
    serializer_class = FeatureSerializer


class TrustCardViewSet(viewsets.ModelViewSet):
    queryset = TrustCard.objects.filter(is_active=True)
    serializer_class = TrustCardSerializer


class PricingPlanViewSet(viewsets.ModelViewSet):
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = PricingPlanSerializer


class ComplianceSectionViewSet(viewsets.ModelViewSet):
    queryset = ComplianceSection.objects.filter(is_active=True)
    serializer_class = ComplianceSectionSerializer


class CTASectionViewSet(viewsets.ModelViewSet):
    queryset = CTASection.objects.filter(is_active=True)
    serializer_class = CTASectionSerializer


class LandingLeadViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = LandingLead.objects.all()
    serializer_class = LandingLeadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class SitePageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SitePage.objects.filter(is_active=True)
    serializer_class = SitePageSerializer
    lookup_field = "slug"
