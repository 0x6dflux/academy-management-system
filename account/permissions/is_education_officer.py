from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from account.models.user import User


class IsEducationOfficer(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.role == User.RoleChoices.EDUCATION_OFFICER  # type: ignore
