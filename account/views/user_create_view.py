from django.contrib.auth import get_user_model
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from account.serializers import UserSerializer

USER = get_user_model()


class UserCreateAPIView(CreateAPIView):
    # queryset is not necessary for POST method

    serializer_class = UserSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer: UserSerializer) -> None:  # type: ignore
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )


# from rest_framework.request import Request
# from rest_framework.response import Response
# from rest_framework.views import APIView
# class UserCreateAPIView(APIView):
#     def post(self, request: Request) -> Response:
#         user_serializer = UserSerializer(data=request.data)
#         if user_serializer.is_valid():
#             # save the new user in the database

#             return Response(user_serializer.data)

#         return Response(user_serializer.errors)
