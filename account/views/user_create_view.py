from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from account.permissions import IsRoleAdmin
from account.serializers import CreateUserSerializer


class UserCreateAPIView(CreateAPIView):
    # queryset is not necessary for POST method
    http_method_names = ("post",)
    serializer_class = CreateUserSerializer
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated, IsRoleAdmin)
