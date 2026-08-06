from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from account.permissions import IsEducationOfficerOrAdmin


class HomeAPIView(APIView):
    http_method_names = ("get",)
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    def get(self, request: Request) -> Response:
        return Response({"status": HTTP_200_OK, "message": "Education API"})
