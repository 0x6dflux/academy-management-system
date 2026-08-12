from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import School, SchoolContactPerson
from education.serializers import (
    SchoolContactPersonModelSerializer,
    SchoolModelSerializer,
)
from system.utils import SoftDeleteModelViewSetMixin


class SchoolModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = School.objects.all()
    serializer_class = SchoolModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)


class SchoolContactPersonModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = SchoolContactPerson.objects.all()
    serializer_class = SchoolContactPersonModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
