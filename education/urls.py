from django.urls import include, path
from rest_framework.routers import SimpleRouter

from education.views import (
    CourseModelViewSet,
    HomeAPIView,
    ReportCustomModelViewSet,
    ReportReviewCustomModelViewSet,
    SchoolContactPersonModelViewSet,
    SchoolModelViewSet,
    SemesterModelViewSet,
    SessionModelViewSet,
    TeacherCourseModelViewSet,
    TeacherScheduleAPIView,
)

router = SimpleRouter(use_regex_path=False)
router.register("school", SchoolModelViewSet)
router.register(
    "school-contact-person",
    SchoolContactPersonModelViewSet,
    "school-contact-person",
)
router.register("semester", SemesterModelViewSet)
router.register("course", CourseModelViewSet)
router.register("session", SessionModelViewSet)
router.register("teacher-course", TeacherCourseModelViewSet, "teacher-course")
router.register("report", ReportCustomModelViewSet)
router.register("report-review", ReportReviewCustomModelViewSet, "report-review")

app_name = "education"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("", include(router.urls)),
    path(
        "teacher-schedule/",
        TeacherScheduleAPIView.as_view(),
        name="teacher-schedule",
    ),
]
