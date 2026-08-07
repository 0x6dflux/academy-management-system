from django.contrib.auth.models import AbstractUser
from django.db import models

from account.models.user_manager import UserAllObjectsManager, UserSoftDeleteManager
from system.models import SoftDeleteMixin


class User(AbstractUser, SoftDeleteMixin):
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

    all_objects: UserAllObjectsManager = UserAllObjectsManager()  # type: ignore
    objects: UserSoftDeleteManager = UserSoftDeleteManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    class Meta:
        base_manager_name = "all_objects"
