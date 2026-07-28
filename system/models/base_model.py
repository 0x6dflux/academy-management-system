from django.db import models

from system.models.base_manager import SoftDeleteManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    # to create the first user, null=False and blank=False will raise error
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    # to create the first user, null=False and blank=False will raise error
    is_deleted = models.BooleanField(default=False)

    soft_objects = SoftDeleteManager()
    # this manager adds the soft deletion feature next
    # to the default `objects` manager

    class Meta:
        abstract = True

    def _perform_obj_soft_delete(self, updated_by) -> None:
        self.is_deleted = True
        self.updated_by = updated_by
        self.save(update_fields=["is_deleted", "updated_by"])

    def _perform_cascade_soft_delete(self, updated_by) -> None:
        reverse_relations = []
        for field in self._meta.get_fields():
            if (
                field.is_relation
                and field.auto_created
                and issubclass(field.related_model, BaseModel)
            ):
                reverse_relations.append(field)

        for reverse_relation in reverse_relations:
            reverse_relation_attr = getattr(self, reverse_relation.get_accessor_name())
            # there might be a `RelatedObjectDoesNotExist` exception
            # suppose a user with teacher role has been created, but no TeacherProfile
            # is created. if you soft delete this user, the cascade soft deletion will
            # raise this error.

            if reverse_relation.one_to_one:
                # `reverse_relation_attr` is the related object
                # reverse_relation_attr._perform_obj_soft_delete(updated_by)
                # chain of soft deletion
                reverse_relation_attr.soft_delete(updated_by)

            elif reverse_relation.one_to_many:
                # `reverse_relation_attr` is the related manager
                reverse_relation_attr.all().soft_delete(updated_by)

    def soft_delete(self, updated_by) -> None:
        self._perform_obj_soft_delete(updated_by)
        self._perform_cascade_soft_delete(updated_by)
