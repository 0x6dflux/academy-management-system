from django.urls import include, path
from rest_framework.routers import SimpleRouter

from finance.views import HomeAPIView, WageRateCustomModelViewSet

router = SimpleRouter(use_regex_path=False)
router.register("wage-rate", WageRateCustomModelViewSet, "wage-rate")

app_name = "finance"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("", include(router.urls)),
]
