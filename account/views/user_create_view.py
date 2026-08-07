from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from account.permissions import IsRoleAdmin
from account.serializers import CreateUserSerializer


class UserCreateAPIView(CreateAPIView):
    # queryset is not necessary for POST method
    http_method_names = ("post",)
    serializer_class = CreateUserSerializer
    permission_classes = (IsAuthenticated, IsRoleAdmin)

    def post(self, request: Request, *args, **kwargs) -> Response:
        super_response = super().post(request, *args, **kwargs)

        result = {**super_response.data, "status": HTTP_201_CREATED}

        return Response(result, HTTP_201_CREATED)
