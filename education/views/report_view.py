from django.db.models import OuterRef, Subquery
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from account.models import User
from account.permissions import (
    IsEducationOfficerOrAdmin,
    IsTeacherOrEducationOfficerOrAdmin,
)
from education.models import Report, ReportHistory
from education.serializers import (
    ReportHistoryModelSerializer,
    ReportReadOnlyModelSerializer,
    ReportReviewWriteOnlyModelSerializer,
    ReportSubmissionWriteOnlyModelSerializer,
)

USER = User


class ReportCustomModelViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    # only users with TCH role can update their reports
    # whenever each report has been reviewed by EDO
    http_method_names = ("get", "post", "put", "patch")
    queryset = Report.objects.all()
    permission_classes = (IsAuthenticated, IsTeacherOrEducationOfficerOrAdmin)

    def get_queryset(self):
        if self.request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
            return (
                super().get_queryset().filter(teacher_profile__user=self.request.user)
            )

        elif self.request.user.role == USER.RoleChoices.EDUCATION_OFFICER:  # type: ignore
            return (
                super()
                .get_queryset()
                .annotate(
                    latest_change=Subquery(
                        ReportHistory.objects.filter(report=OuterRef("pk"))
                        .order_by("-id")
                        .values("change")[:1]
                    )
                )
                # .prefetch_related("histories")
                .exclude(
                    latest_change__in=(
                        ReportHistory.ChangeChoices.REJECTED,
                        ReportHistory.ChangeChoices.APPROVED,
                    )
                )
            )

        else:
            # user with ADMIN role
            return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ReportReadOnlyModelSerializer
        else:
            # actions for `POST`, `PUT`, and `PATCH`
            if self.request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
                return ReportSubmissionWriteOnlyModelSerializer
            else:
                # EDO or ADMIN
                return ReportReviewWriteOnlyModelSerializer

    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)

        if self.request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
            # write log on the ReportHistory model
            ReportHistory.objects.create(
                report_id=serializer.data["id"],
                user=self.request.user,  # type: ignore
                role=self.request.user.role,  # type: ignore
                change=ReportHistory.ChangeChoices.CREATED,
            )

    def perform_update(self, serializer) -> None:
        if self.request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
            super().perform_update(serializer)

            # write log on the ReportHistory model
            ReportHistory.objects.create(
                report_id=serializer.data["id"],
                user=self.request.user,  # type: ignore
                role=self.request.user.role,  # type: ignore
                change=ReportHistory.ChangeChoices.UPDATED,
            )


class ReportHistoryCustomModelViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    http_method_names = ("get", "patch")
    queryset = ReportHistory.objects.all()
    serializer_class = ReportHistoryModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
    filter_backends = (OrderingFilter,)
    ordering = ("-modified_at",)
