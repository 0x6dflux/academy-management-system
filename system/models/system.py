from django.db import models

from system.models import BaseModel


class System(BaseModel):
    school = models.ForeignKey("education.School", models.CASCADE)
    semester = models.ForeignKey("education.Semester", models.CASCADE)
    academic_class = models.ForeignKey("education.AcademicClass", models.CASCADE)
    last_school_serial_number = models.IntegerField(default=0)
    last_semester_serial_number = models.IntegerField(default=0)
    last_academic_class_serial_number = models.IntegerField(default=0)
    last_session_serial_number = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.school}-{self.semester}-{self.academic_class}"
