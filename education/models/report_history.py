from django.db import models

from account.models import User

USER = User


class ReportHistory(models.Model):
    """This model will be systematically modified."""

    class ChangeChoices(models.IntegerChoices):
        APPROVED = 1, "Approved"
        REJECTED = 0, "Rejected"
        CREATED = 2, "Created"
        UPDATED = 3, "Updated"

    report = models.ForeignKey(
        "education.report",
        models.SET_NULL,
        "histories",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        "account.User",
        models.SET_NULL,
        "+",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=3, choices=USER.RoleChoices)
    change = models.PositiveSmallIntegerField(choices=ChangeChoices)
    description = models.TextField(null=True, blank=True)
    modified_at = models.DateTimeField(auto_now_add=True)
