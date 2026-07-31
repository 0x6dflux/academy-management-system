from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.serializers import UserSerializer

if TYPE_CHECKING:
    from account.models import User

USER: User = get_user_model()  # type: ignore


class UserRetrieveAPIView(APIView):
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        # get the logged in user from the request
        user_instance = USER.objects.get(pk=str(request.user.pk))

        user_serializer = UserSerializer(user_instance)

        return Response(user_serializer.data)
