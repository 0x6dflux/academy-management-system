from django.db import models

from system.models import BaseModel


class TeacherAcademicClass(BaseModel):
    """customized through table between Teacher and AcademicClass"""

    teacher_profile = models.ForeignKey("account.TeacherProfile", models.CASCADE)
    academic_class = models.ForeignKey("education.AcademicClass", models.CASCADE)
    started_at = models.DateTimeField()
    # [validation] `started_at` shall be within the class start and end time
    ended_at = models.DateTimeField()
    # [validation] `ended_at` shall be within the class start and end time

    # [validation] time intervals shall not overlap each other

    def __str__(self) -> str:
        return f"{self.teacher_profile}-{self.academic_class}"
