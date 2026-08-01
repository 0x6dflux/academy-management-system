from django.contrib.auth.models import UserManager
from django.db.models.query import QuerySet

from system.models.base_manager import SoftDeleteQuerySet


class UserSoftDeleteManager(UserManager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().filter(is_deleted=False)
