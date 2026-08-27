from django.db.models.query import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from account.models import User
from account.permissions import (
    IsFinanceOfficerOrAdmin,
    IsTeacherOrFinanceOfficerOrAdmin,
)
from finance.models import Wage
from finance.serializers import WageCalculationSerializer, WageModelSerializer
from services.wage_service import WageService

USER = User


# consider filter-backend to act as retrieve method
class WageReadOnlyModelViewSet(ReadOnlyModelViewSet):
    http_method_names = ("get", "post")
    queryset = Wage.objects.all()
    serializer_class = WageModelSerializer
    permission_classes = (IsAuthenticated, IsTeacherOrFinanceOfficerOrAdmin)

    def get_queryset(self) -> QuerySet:
        if self.request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
            return (
                super().get_queryset().filter(teacher_profile__user=self.request.user)
            )

        return super().get_queryset()


class WageCalculationAPIView(APIView):
    http_method_names = ("post",)
    permission_classes = (IsAuthenticated, IsFinanceOfficerOrAdmin)

    def post(self, request: Request) -> Response:
        wage_calculation_serializer = WageCalculationSerializer(data=request.data)

        wage_calculation_serializer.is_valid(raise_exception=True)

        WageService(
            wage_calculation_serializer.validated_data["year"],
            wage_calculation_serializer.validated_data["month"],
            request.user,  # type: ignore
        ).calculate_wages()

        return Response({"message": "All wages have been calculated."})
