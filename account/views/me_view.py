from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from account.models import User
from account.serializers import UserSerializer

USER = User


class UserRetrieveAPIView(APIView):
    http_method_names = ("get",)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        user_serializer = UserSerializer(request.user)

        result = {"status": HTTP_200_OK, **user_serializer.data}

        return Response(result, HTTP_200_OK)
