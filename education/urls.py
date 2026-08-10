from django.urls import include, path
from rest_framework.routers import SimpleRouter

from education.views import (
    HomeAPIView,
    SchoolContactPersonModelViewSet,
    SchoolModelViewSet,
)

router = SimpleRouter(use_regex_path=False)
router.register("school", SchoolModelViewSet)
router.register(
    "school-contact-person",
    SchoolContactPersonModelViewSet,
    "school-contact-person",
)

app_name = "education"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("", include(router.urls)),
]
