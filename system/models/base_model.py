from django.db import models


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

    class Meta:
        abstract = True
