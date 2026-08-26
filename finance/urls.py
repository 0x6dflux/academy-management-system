from django.urls import include, path
from rest_framework.routers import SimpleRouter

from finance.views import (
    HomeAPIView,
    WageRateCustomModelViewSet,
    WageReadOnlyModelViewSet,
)

router = SimpleRouter(use_regex_path=False)
router.register("wage-rate", WageRateCustomModelViewSet, "wage-rate")
router.register("wage", WageReadOnlyModelViewSet)

app_name = "finance"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("", include(router.urls)),
]
