from rest_framework import viewsets, permissions, mixins
from ..models import HeroSection, Feature, TrustCard, PricingPlan, ComplianceSection, CTASection, LandingLead, SitePage
from .serializers import (
    HeroSectionSerializer, FeatureSerializer, TrustCardSerializer,
    PricingPlanSerializer, ComplianceSectionSerializer, CTASectionSerializer,
    LandingLeadSerializer, SitePageSerializer,
)
from apps.accounts.permissions import RoleBasedPermission, IsSuperAdmin


class HeroSectionViewSet(viewsets.ModelViewSet):
    queryset = HeroSection.objects.filter(is_active=True)
    serializer_class = HeroSectionSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.filter(is_active=True)
    serializer_class = FeatureSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class TrustCardViewSet(viewsets.ModelViewSet):
    queryset = TrustCard.objects.filter(is_active=True)
    serializer_class = TrustCardSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class PricingPlanViewSet(viewsets.ModelViewSet):
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = PricingPlanSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class ComplianceSectionViewSet(viewsets.ModelViewSet):
    queryset = ComplianceSection.objects.filter(is_active=True)
    serializer_class = ComplianceSectionSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class CTASectionViewSet(viewsets.ModelViewSet):
    queryset = CTASection.objects.filter(is_active=True)
    serializer_class = CTASectionSerializer
    permission_classes = [RoleBasedPermission]
    role_map = {
        "list": "viewer",
        "retrieve": "viewer",
        "create": "super_admin",
        "update": "super_admin",
        "partial_update": "super_admin",
        "destroy": "super_admin",
    }


class LandingLeadViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = LandingLead.objects.all()
    serializer_class = LandingLeadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class SitePageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SitePage.objects.filter(is_active=True)
    serializer_class = SitePageSerializer
    lookup_field = "slug"
    permission_classes = [RoleBasedPermission]
