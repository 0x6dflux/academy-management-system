from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import Course
from education.serializers import CourseModelSerializer


class CourseModelViewSet(ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = Course.objects.all()
    serializer_class = CourseModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
