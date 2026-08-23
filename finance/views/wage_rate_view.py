from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsFinanceOfficerOrAdmin
from finance.models import WageRate
from finance.serializers import WageRateModelSerializer
from system.utils import SoftDeleteModelViewSetMixin


class WageRateCustomModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = WageRate.objects.all()
    serializer_class = WageRateModelSerializer
    permission_classes = (IsAuthenticated, IsFinanceOfficerOrAdmin)
