from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import TeacherCourse
from education.serializers import TeacherCourseModelSerializer


class TeacherCourseModelViewSet(ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = TeacherCourse.objects.all()
    serializer_class = TeacherCourseModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    def get_object(self) -> Any:
        pk = self.kwargs["pk"]
        teacher_profile_id, course_id = pk.split("__")

        obj = get_object_or_404(
            TeacherCourse,
            teacher_profile_id=teacher_profile_id,
            course_id=course_id,
        )

        self.check_object_permissions(self.request, obj)

        return obj
