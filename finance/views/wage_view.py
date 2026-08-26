from django.db.models.query import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from account.models import User
from account.permissions import (
    IsTeacherOrFinanceOfficerOrAdmin,
)
from finance.models import Wage
from finance.serializers import WageModelSerializer

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
