from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, SubscriptionViewSet, PublicPlanListView

router = DefaultRouter()
router.register(r"plans", SubscriptionPlanViewSet, basename="subscription-plans")
router.register(r"", SubscriptionViewSet, basename="subscription")

urlpatterns = router.urls + [
    path("public-plans/", PublicPlanListView.as_view(), name="public-plans"),
]
