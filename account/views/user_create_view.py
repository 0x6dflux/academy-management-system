from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from account.permissions import IsRoleAdmin
from account.serializers import UserSerializer

if TYPE_CHECKING:
    from account.models import User

USER: User = get_user_model()  # type: ignore


class UserCreateAPIView(CreateAPIView):
    # queryset is not necessary for POST method
    http_method_names = ["post"]
    serializer_class = UserSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated, IsRoleAdmin]

    def perform_create(self, serializer: UserSerializer) -> None:  # type: ignore
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )
