from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import Semester
from education.serializers import SemesterModelSerializer
from system.utils import SoftDeleteModelViewSetMixin


class SemesterModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = Semester.objects.all()
    serializer_class = SemesterModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
