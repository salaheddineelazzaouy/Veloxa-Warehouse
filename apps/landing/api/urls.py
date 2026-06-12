from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HeroSectionViewSet, FeatureViewSet, TrustCardViewSet,
    PricingPlanViewSet, ComplianceSectionViewSet, CTASectionViewSet,
    LandingLeadViewSet, SitePageViewSet,
)

router = DefaultRouter()
router.register(r"hero", HeroSectionViewSet)
router.register(r"features", FeatureViewSet)
router.register(r"trust-cards", TrustCardViewSet)
router.register(r"pricing-plans", PricingPlanViewSet)
router.register(r"compliance", ComplianceSectionViewSet)
router.register(r"cta", CTASectionViewSet)
router.register(r"leads", LandingLeadViewSet)
router.register(r"pages", SitePageViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
