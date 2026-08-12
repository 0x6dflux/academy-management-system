from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import Session
from education.serializers import SessionModelSerializer
from system.utils import SoftDeleteModelViewSetMixin


class SessionModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = Session.objects.all()
    serializer_class = SessionModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
