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

    # the queryset of the related fields in the process of cascade soft
    # deletion uses the default manager which its objects does not own the
    # `.soft_delete()` method. So, the default manager has been changed to
    # the `SoftDeleteManager` to ease the process of soft deletion.
    # moreover, it is more compatible to the Django conventions to use
    # objects instead of `soft_objects` - see commits history.
    objects = SoftDeleteManager()
    # this manager adds the soft deletion feature next
    # to the default `objects` manager

    all_objects = models.Manager()
    # since we have defined a custom manager, the default manager
    # will not be added to the models. So, the default manager has
    # been specified here

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
                and issubclass(field.related_model, BaseModel)  # type: ignore
                # there might be an `TypeError` exception for the above line: issubclass(None, BaseModel)
                # it would be better to check the below condition, then move the above line in the if block
                # and field.related_model is not None
                and field.related_model.SoftDeletionOptions.cascade  # type: ignore
            ):
                reverse_relations.append(field)

        for reverse_relation in reverse_relations:
            # these attributes shall have `related_model`, since they are relational attributes
            # but, there might be an `AttributeError` for `SoftDeletionPolicy`
            # at first, the exception was handled with a try-except block
            # however, the SoftDeletionPolicy subclass has been added to the BaseModel
            # so, there is no need to catch the exception
            # cascade_policy = reverse_relation.related_model.SoftDeletionPolicy.cascade  # type: ignore
            # if cascade_policy is False:
            #     # there might be a customized equality magic method, so, it is better
            #     # to use `is` rather than `==`
            #     continue

            # there might be a `RelatedObjectDoesNotExist` exception
            # suppose a user with teacher role has been created, but no TeacherProfile
            # is created. if you soft delete this user, the cascade soft deletion will
            # raise this error.
            try:
                reverse_relation_attr = getattr(
                    self,
                    reverse_relation.get_accessor_name(),  # type: ignore
                )
            except reverse_relation.related_model.DoesNotExist:  # type: ignore
                continue

            if reverse_relation.one_to_one:
                # `reverse_relation_attr` is the related object
                # reverse_relation_attr._perform_obj_soft_delete(updated_by)
                # chain of soft deletion
                reverse_relation_attr.soft_delete(updated_by)

            elif reverse_relation.one_to_many:
                # `reverse_relation_attr` is the related manager
                reverse_relation_attr.all().soft_delete(updated_by)

            # as per test cases, `ManyToMany` relations shall not soft deleted
            # for example, school and contact person models were related by a
            # `ManyToMany` field. The tests showed that this relation is wrong.

    # use transaction.atomic decorator!?
    def soft_delete(self, updated_by) -> None:
        self._perform_cascade_soft_delete(updated_by)
        # first, perform soft deletion on children, then on the parent
        # more robust for production!?
        self._perform_obj_soft_delete(updated_by)

    class SoftDeletionOptions:
        cascade = True
