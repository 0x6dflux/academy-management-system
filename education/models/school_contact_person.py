from django.db import models

from system.models import BaseModel


class SchoolContactPerson(BaseModel):
    class SchoolRoleChoices(models.IntegerChoices):
        MANAGER = 1, "Manager"
        DEPUTY = 2, "Deputy"

    school = models.ForeignKey("education.School", models.CASCADE, "contact_people")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_role = models.PositiveSmallIntegerField(choices=SchoolRoleChoices)
    mobile_number = models.CharField(max_length=15)
    landline_extension_number = models.PositiveSmallIntegerField()

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
