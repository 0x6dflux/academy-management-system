from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

from system.models import BaseModel


class User(AbstractUser, BaseModel):
    class RoleChoices(models.TextChoices):
        TEACHER = "TCH", "Teacher"
        EDUCATION_OFFICER = "EDO", "Education Officer"
        FINANCE_OFFICER = "FIO", "Finance Officer"
        ADMIN = "ADM", "Admin"

    first_name = None  # type: ignore
    last_name = None  # type: ignore
    date_joined = None  # type: ignore
    role = models.CharField(max_length=3, choices=RoleChoices.choices)

    REQUIRED_FIELDS: ClassVar[list[str]] = ["role"]
