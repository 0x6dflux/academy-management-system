from django.db import models

from system.models import BaseModel


class Semester(BaseModel):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_summer_semester = models.BooleanField(default=False)
    serial_number = models.CharField(max_length=6)  # SMxxxx

    def __str__(self) -> str:
        return self.name
