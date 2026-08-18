from django.db.models.query import QuerySet
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from account.permissions import IsEducationOfficerOrAdmin, IsTeacherOrAdmin
from education.models import Report, ReportHistory
from education.serializers import (
    ReportEDORoleModelSerializer,
    ReportTCHRoleModelSerializer,
)


class ReportCustomModelViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    http_method_names = ("get", "post", "put", "patch")
    queryset = Report.objects.all()
    serializer_class = ReportTCHRoleModelSerializer
    permission_classes = (IsAuthenticated, IsTeacherOrAdmin)

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(teacher_profile__user=self.request.user)

    def perform_create(self, serializer: BaseSerializer) -> None:
        super().perform_create(serializer)

        # creating the ReportHistory
        ReportHistory.objects.create(
            report_id=serializer.data["id"],
            user=self.request.user,  # type: ignore
            role=self.request.user.role,  # type: ignore
            change=ReportHistory.ChangeChoices.CREATED,
        )

    def perform_update(self, serializer: BaseSerializer) -> None:
        super().perform_update(serializer)

        # updating the ReportHistory
        ReportHistory.objects.create(
            report_id=serializer.data["id"],
            user=self.request.user,  # type: ignore
            role=self.request.user.role,  # type: ignore
            change=ReportHistory.ChangeChoices.UPDATED,
        )


class ReportReviewCustomModelViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    http_method_names = ("get", "post")
    queryset = ReportHistory.objects.all()
    serializer_class = ReportEDORoleModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
