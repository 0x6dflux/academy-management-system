from django.db import models

from system.models import BaseModel


class TeacherProfile(BaseModel):
    user = models.OneToOneField("account.User", models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11)
    emergency_phone_number = models.CharField(max_length=11)
    # phone number or house number

    def __str__(self) -> str:
        return f"{self.first_name}-{self.last_name}-{self.user.role}"
