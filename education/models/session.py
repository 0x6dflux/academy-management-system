from django.db import models

from system.models import BaseModel


class Session(BaseModel):
    class DurationChoices(models.IntegerChoices):
        MIN60 = 60, "60 min"
        MIN90 = 90, "90 min"
        MIN120 = 120, "120 min"

    academic_class = models.ForeignKey("education.AcademicClass", models.CASCADE)
    name = models.CharField(max_length=50)
    duration = models.IntegerField(choices=DurationChoices.choices)
    date = models.DateField(auto_now_add=True)
    # [validation] `date` shall be within the class start and end time
    start_time = models.TimeField()
    end_time = models.TimeField()
    serial_number = models.CharField(max_length=6)  # SSxxxx
    tutorial_summary = models.TextField()
    number_of_attendees = models.SmallIntegerField()
    number_of_absentees = models.SmallIntegerField()

    def __str__(self) -> str:
        return self.name
