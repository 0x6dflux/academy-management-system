from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

if TYPE_CHECKING:
    from account.models.user import User


USER: User = get_user_model()  # type: ignore


class IsRoleAdmin(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.role == USER.RoleChoices.ADMIN  # type: ignore
        # `IsAuthenticated` permission will be performed prior to this
        # permission, so request.user will not be `anonymous`
