from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from account.models import TeacherProfile
from account.permissions import (
    IsEducationOfficerOrAdmin,
    IsTeacherOrAdmin,
    IsTeacherOrEducationOfficerOrAdmin,
)
from account.serializers import (
    TeacherProfileEducationOfficerRoleSerializer,
    TeacherProfileTeacherRoleSerializer,
)

if TYPE_CHECKING:
    from account.models.user import User

USER: User = get_user_model()  # type: ignore


class TeacherProfileAPIView(APIView):
    http_method_names = ["get", "post", "put", "patch", "delete"]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        permissions: list = super().get_permissions()  # type: ignore

        if self.request.method in ["POST", "PUT", "PATCH"]:
            permissions.append(IsTeacherOrAdmin())
        elif self.request.method == "DELETE":
            permissions.append(IsEducationOfficerOrAdmin())
        else:  # GET
            permissions.append(IsTeacherOrEducationOfficerOrAdmin())

        return permissions

    def _retrieve(self, request: Request) -> Response:
        queryset = TeacherProfile.objects.filter(user=request.user)
        if not queryset.exists():
            return Response({"message": "Create your profile."}, HTTP_400_BAD_REQUEST)

        teacher_instance = queryset.first()
        teacher_serializer = TeacherProfileTeacherRoleSerializer(teacher_instance)

        return Response(teacher_serializer.data)

    def _list(self, request: Request) -> Response:
        queryset = TeacherProfile.objects.all()
        education_officer_serializer = TeacherProfileEducationOfficerRoleSerializer(
            queryset,
            many=True,
        )

        return Response(education_officer_serializer.data)

    def _update(self, request: Request, *, partial=False) -> Response:
        teacher_instance = TeacherProfile.objects.get(user=request.user)
        teacher_serializer = TeacherProfileTeacherRoleSerializer(
            teacher_instance,
            request.data,
            partial=partial,
        )

        if not teacher_serializer.is_valid():
            return Response(teacher_serializer.errors, HTTP_400_BAD_REQUEST)

        teacher_serializer.validated_data["updated_by"] = request.user
        teacher_serializer.save()

        return Response(teacher_serializer.data)

    def get(self, request: Request) -> Response:
        # dispatching the request by `request.user`
        if request.user.role == USER.RoleChoices.TEACHER:  # type: ignore
            return self._retrieve(request)
        else:
            # USER.RoleChoices.EDUCATION_OFFICER
            # USER.RoleChoices.ADMIN
            return self._list(request)

    def post(self, request: Request) -> Response:
        # the admin is not stupid enough to create a teacher profile for themselves
        # if request.user.role != "TCH":  # type: ignore
        #     return Response(
        #         {"message": "Only teachers can have this profile!"},
        #         HTTP_400_BAD_REQUEST,
        #     )

        if TeacherProfile.objects.filter(user=request.user).exists():
            return Response(
                {"message": "The profile already exists!"},
                HTTP_400_BAD_REQUEST,
            )

        teacher_serializer = TeacherProfileTeacherRoleSerializer(data=request.data)

        if not teacher_serializer.is_valid():
            return Response(teacher_serializer.errors, HTTP_400_BAD_REQUEST)

        teacher_serializer.validated_data["user"] = request.user
        teacher_serializer.validated_data["created_by"] = request.user
        teacher_serializer.validated_data["updated_by"] = request.user
        teacher_serializer.save()

        return Response(teacher_serializer.data, HTTP_201_CREATED)

    def put(self, request: Request) -> Response:
        return self._update(request)

    def patch(self, request: Request) -> Response:
        return self._update(request, partial=True)

    def delete(self, request: Request) -> Response:
        teacher_profile_id = request.query_params.get("id")

        if not teacher_profile_id:
            return Response(
                {"message": "Pass the teacher profile id!"},
                HTTP_400_BAD_REQUEST,
            )

        TeacherProfile.objects.get(id=teacher_profile_id).soft_delete(
            updated_by=request.user
        )

        return Response(status=HTTP_204_NO_CONTENT)
