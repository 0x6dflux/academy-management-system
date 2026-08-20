from django.db.models import OuterRef, Subquery
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from account.models import User
from account.permissions import (
    IsEducationOfficerOrAdmin,
    IsTeacherOrEducationOfficerOrAdmin,
)
from education.models import Report, ReportHistory
from education.serializers import (
    ReportBulkApprovalSerializer,
    ReportHistoryModelSerializer,
    ReportReadOnlyModelSerializer,
    ReportReviewWriteOnlyModelSerializer,
    ReportSubmissionWriteOnlyModelSerializer,
)

USER = User


class ReportFilter(FilterSet):
    school = CharFilter("session__course__semester__school__name", "icontains")
    course = CharFilter("session__course__name", "icontains")
    teacher_first_name = CharFilter("teacher_profile__first_name", "icontains")
    teacher_last_name = CharFilter("teacher_profile__last_name", "icontains")
    date = DateFromToRangeFilter("session__date")

    class Meta:
        model = Report
        fields = ("school", "course", "teacher_first_name", "teacher_last_name", "date")


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ReportFilter

    def get_queryset(self):
        # as per swagger warning
        if getattr(self, "swagger_fake_view", False):
            return Report.objects.none()

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
        # as per swagger warning
        if getattr(self, "swagger_fake_view", False):
            return ReportReadOnlyModelSerializer

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

        # for TCH consider transaction atomic!!

    def perform_update(self, serializer) -> None:
        if self.request.user.role != USER.RoleChoices.TEACHER:  # type: ignore
            raise PermissionDenied(
                "Only users with TCH role can update report content!"
            )

        super().perform_update(serializer)

        # write log on the ReportHistory model
        ReportHistory.objects.create(
            report_id=serializer.data["id"],
            user=self.request.user,  # type: ignore
            role=self.request.user.role,  # type: ignore
            change=ReportHistory.ChangeChoices.UPDATED,
        )


class ReportBulkApprovalAPIView(APIView):
    http_method_names = ("post",)
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    # def get_queryset(self):
    #     return Report.objects.annotate(
    #         latest_change=Subquery(
    #             ReportHistory.objects.filter(report=OuterRef("pk"))
    #             .order_by("-id")
    #             .values("change")[:1]
    #         )
    #     ).exclude(
    #         latest_change__in=(
    #             ReportHistory.ChangeChoices.APPROVED,
    #             ReportHistory.ChangeChoices.REJECTED,
    #         )
    #     )

    # def get(self, request: Request) -> Response:
    #     bulk_serializer = ReportBulkApprovalSerializer(self.get_queryset(), many=True)

    #     return Response(bulk_serializer.data)

    def post(self, request: Request) -> Response:
        bulk_serializer = ReportBulkApprovalSerializer(data=request.data)
        bulk_serializer.is_valid(raise_exception=True)

        reports = bulk_serializer.validated_data["reports"]

        # transaction atomic!!
        ReportHistory.objects.bulk_create(
            ReportHistory(
                report=report,
                user=request.user,  # type: ignore
                role=request.user.role,  # type: ignore
                change=ReportHistory.ChangeChoices.APPROVED,
            )
            for report in reports
        )

        return Response(bulk_serializer.data, HTTP_201_CREATED)


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
