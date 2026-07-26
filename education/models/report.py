from django.db import models

from system.models import BaseModel


class Report(BaseModel):
    teacher_academic_class = models.ForeignKey(
        "education.TeacherAcademicClass",
        models.CASCADE,
    )
    session = models.OneToOneField("education.Session", models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)
    is_delayed = models.BooleanField()
    # shall not be filled by default, this is a required field
    # [validation] define a function/method to determine the delay
    # this validation shall be simple at first
    # then, shall be modified to be calculated as a delayed report in wage
    serial_number = models.CharField(max_length=6)  # RPxxxx

    def __str__(self) -> str:
        return self.name
