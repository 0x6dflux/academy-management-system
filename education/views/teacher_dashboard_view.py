from datetime import datetime, timedelta

import pytz
from django.db.models import OuterRef, Subquery
from django.db.models.query import QuerySet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from account.permissions import IsTeacherOrAdmin
from config.settings import TIME_ZONE
from education.models import Course, ReportHistory, Session
from education.serializers import (
    TeacherReportStatQuerySerializer,
    TeacherReportStatSerializer,
    TeacherScheduleCourseSerializer,
)

USER = User


class TeacherScheduleAPIView(ListAPIView):
    http_method_names = ("get",)
    queryset = Course.objects.all()
    serializer_class = TeacherScheduleCourseSerializer
    permission_classes = (IsAuthenticated, IsTeacherOrAdmin)

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset().prefetch_related("sessions")

        if self.request.user.role == USER.RoleChoices.ADMIN:  # type: ignore
            # admin can see all courses and sessions
            return qs

        return qs.filter(teachers__teacher_profile__user=self.request.user)


class TeacherReportStatAPIView(APIView):
    http_method_names = ("get",)
    permission_classes = (IsAuthenticated, IsTeacherOrAdmin)

    def get(self, request: Request) -> Response:
        query_serializer = TeacherReportStatQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        days = query_serializer.validated_data["days"]

        tz = pytz.timezone(TIME_ZONE)
        start_date = datetime.now(tz).date() - timedelta(days=days)

        sessions = Session.objects.filter(
            course__teachers__teacher_profile__user=request.user,
            date__gte=start_date,
        )

        response_data = {
            "from_date": start_date,
            "period_in_days": days,
            "total_sessions": sessions.count(),
            "not_submitted": sessions.filter(report__isnull=True).count(),
        }

        sessions = sessions.filter(report__isnull=False).annotate(
            latest_change=Subquery(
                ReportHistory.objects.filter(report=OuterRef("report__pk"))
                .order_by("-id")
                .values("change")[:1]
            )
        )

        response_data["pending_review"] = sessions.filter(
            latest_change__in=(
                ReportHistory.ChangeChoices.CREATED,
                ReportHistory.ChangeChoices.UPDATED,
            )
        ).count()

        response_data["rejected"] = sessions.filter(
            latest_change=ReportHistory.ChangeChoices.REJECTED
        ).count()

        response_data["approved"] = sessions.filter(
            latest_change=ReportHistory.ChangeChoices.APPROVED
        ).count()

        response_serializer = TeacherReportStatSerializer(response_data)

        return Response(response_serializer.data)
