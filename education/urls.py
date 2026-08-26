from django.urls import include, path
from rest_framework.routers import SimpleRouter

from education.views import (
    CourseModelViewSet,
    HomeAPIView,
    ReportBulkApprovalAPIView,
    ReportCustomModelViewSet,
    ReportHistoryCustomModelViewSet,
    SchoolContactPersonModelViewSet,
    SchoolModelViewSet,
    SemesterModelViewSet,
    SessionModelViewSet,
    SubstituteTeacherAPIView,
    TeacherCourseModelViewSet,
    TeacherReportStatAPIView,
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
router.register("report-history", ReportHistoryCustomModelViewSet, "report-history")

app_name = "education"

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="home"),
    path("", include(router.urls)),
    path(
        "report-bulk-approval/",
        ReportBulkApprovalAPIView.as_view(),
        name="report-bulk-approval",
    ),
    path(
        "teacher-schedule/",
        TeacherScheduleAPIView.as_view(),
        name="teacher-schedule",
    ),
    path(
        "teacher-report-stat/",
        TeacherReportStatAPIView.as_view(),
        name="teacher-report-stat",
    ),
    path(
        "substitute-teacher/",
        SubstituteTeacherAPIView.as_view(),
        name="substitute-teacher",
    ),
]
