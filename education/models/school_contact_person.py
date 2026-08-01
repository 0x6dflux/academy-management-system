from django.db import models

from system.models import BaseModel


class SchoolContactPerson(BaseModel):
    school = models.ForeignKey(
        "education.School",
        models.CASCADE,
        related_name="contact_people",
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
