from django.db import models

from system.models.base_manager import SoftDeleteManager, SoftDeleteQuerySet


class BaseMixin(models.Model):
    """This mixin is used for all models except User"""

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        abstract = True


# [HISTORY] ==============================================================
# the queryset of the related fields in the process of cascade soft
# deletion uses the default manager which its objects does not own the
# `.soft_delete()` method. So, the default manager has been changed to
# the `SoftDeleteManager` to ease the process of soft deletion.
# moreover, it is more compatible to the Django conventions to use
# objects instead of `soft_objects` - see commits history.
# this manager adds the soft deletion feature next
# to the default `objects` manager
# objects = SoftDeleteManager()
# the above manager shall be moved to the `SoftDeletionModel`
# ========================================================================


class SoftDeleteMixin(models.Model):
    """This mixin shall be used after `BaseMixin` to add the ability of soft deletion"""

    is_deleted = models.BooleanField(default=False)

    # since the default manager is used for related fields, it shall have the
    # `.soft_delete` method which is defined in the `SoftDeleteQuerySet`
    # this default manager shall be on top of all managers - see below link
    # https://docs.djangoproject.com/en/6.0/topics/db/managers/#don-t-filter-away-any-results-in-this-type-of-manager-subclass
    all_objects: models.Manager = models.Manager.from_queryset(SoftDeleteQuerySet)()
    objects: SoftDeleteManager = SoftDeleteManager()

    def _perform_obj_soft_delete(self, updated_by) -> None:
        if not self.is_deleted:
            # to check whether the object has been soft deleted or not
            self.is_deleted = True
            if hasattr(self, "updated_by"):
                # `User` model does not have `updated_by` attribute
                self.updated_by = updated_by
                self.save(update_fields=["is_deleted", "updated_by"])  # type: ignore
            else:
                self.save(update_fields=["is_deleted"])  # type: ignore

    def _perform_cascade_soft_delete(self, updated_by) -> None:
        reverse_relations = []
        for field in self._meta.get_fields():  # type: ignore
            if (
                field.is_relation
                and field.auto_created
                # it would be better to check the below condition, then move the above line in the if block
                and issubclass(field.related_model, SoftDeleteMixin)  # type: ignore
                # the above conditions will exclude models which shall not be soft deleted - e.g. `Report` model
            ):
                # to avoid exception, a nested if has been used
                if field.related_model.SoftDeletionOptions.cascade:  # type: ignore
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
                reverse_relation_attr.all().filter(is_deleted=False).soft_delete(
                    updated_by
                )

            # as per test cases, `ManyToMany` relations shall not soft deleted
            # for example, school and contact person models were related by a
            # `ManyToMany` field. The tests showed that this relation is wrong.

    # use transaction.atomic decorator!?
    def soft_delete(self, updated_by) -> None:
        self._perform_cascade_soft_delete(updated_by)
        # first, perform soft deletion on children, then on the parent
        # more robust for production!?
        self._perform_obj_soft_delete(updated_by)

    class Meta:
        abstract = True

    class SoftDeletionOptions:
        cascade = True


# `User` model shall not inherits from the `BaseModel`
# `User` model has its own structure:
# User(..., SoftDeleteMixin)


class SoftDeleteBaseModel(BaseMixin, SoftDeleteMixin):
    class Meta:
        abstract = True
        base_manager_name = "all_objects"


# to avoid rewriting codes at this level!!
class BaseModel(BaseMixin):
    class Meta:
        abstract = True
