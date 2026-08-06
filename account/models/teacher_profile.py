from django.db import models

from system.models import SoftDeleteBaseModel


class TeacherProfile(SoftDeleteBaseModel):
    user = models.OneToOneField("account.User", models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=15)
    landline_number = models.CharField(max_length=15)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
