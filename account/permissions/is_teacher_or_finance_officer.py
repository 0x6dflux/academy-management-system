from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from account.models.user import User

USER = User


class IsTeacherOrFinanceOfficerOrAdmin(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:

        return request.user.role in [  # type: ignore
            USER.RoleChoices.ADMIN,
            USER.RoleChoices.TEACHER,
            USER.RoleChoices.FINANCE_OFFICER,
        ]
        # `IsAuthenticated` permission will be performed prior to this
        # permission, so request.user will not be `anonymous`
