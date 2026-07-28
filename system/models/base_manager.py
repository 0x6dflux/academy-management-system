from django.db import models
from django.utils.timezone import now


class SoftDeleteQuerySet(models.QuerySet):
    def soft_delete(self, updated_by) -> None:
        # self.update(is_deleted=True, updated_at=now(), updated_by=updated_by)
        # the above line improves the performance, but teh cascade soft deletion is incomplete

        # cascade soft deletion is complete but with poorer performance
        for obj in self:
            obj.soft_delete(updated_by)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_deleted=False)
        # return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
        # the above line is not necessary, since the `SoftDeleteManager` inherits from
        # `models.Manager.from_queryset(SoftDeleteQuerySet)`. So, the `super().get_queryset()`
        # will return a queryset of SoftDeleteQuerySet type.
