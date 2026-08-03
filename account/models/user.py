from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from account.models.user_manager import UserSoftDeleteManager
from system.models import BaseModel


class User(AbstractUser, BaseModel):
    class RoleChoices(models.TextChoices):
        TEACHER = "TCH", "Teacher"
        EDUCATION_OFFICER = "EDO", "Education Officer"
        FINANCE_OFFICER = "FIO", "Finance Officer"
        ADMIN = "ADM", "Admin"

    username = None  # type: ignore
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    date_joined = None  # type: ignore
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=3, choices=RoleChoices)

    objects = UserSoftDeleteManager()  # type: ignore
    all_objects = UserManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]
