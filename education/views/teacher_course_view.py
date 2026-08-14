from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import TeacherCourse
from education.serializers import TeacherCourseModelSerializer
from system.utils import SoftDeleteModelViewSetMixin


class TeacherCourseModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = TeacherCourse.objects.all()
    serializer_class = TeacherCourseModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
