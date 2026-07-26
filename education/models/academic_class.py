from django.db import models

from system.models import BaseModel


class AcademicClass(BaseModel):
    class LevelChoices(models.IntegerChoices):
        BASIC = 0, "Basic"
        INTERMEDIATE = 1, "Intermediate"
        ADVANCED = 2, "Advanced"

    name = models.CharField(max_length=50)
    level = models.IntegerField(choices=LevelChoices.choices)
    start_date = models.DateField()  # default to semester start_date
    # [validation] `start_date` shall be within the class start and end time
    end_date = models.DateField()  # default to semester end_date
    # [validation] `end_date` shall be within the class start and end time
    serial_number = models.CharField(max_length=6)  # CLxxxx

    def __str__(self) -> str:
        return self.name
