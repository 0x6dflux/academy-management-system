from django.db import models

from system.models import BaseModel


class TeacherCourse(BaseModel):
    """customized through table between Teacher and Course"""

    pk = models.CompositePrimaryKey("teacher_profile_id", "course_id")
    teacher_profile = models.ForeignKey(
        "account.TeacherProfile",
        models.CASCADE,
        "courses",
    )
    course = models.ForeignKey("education.course", models.CASCADE, "teachers")
    started_at = models.DateTimeField()
    # [validation] shall be in the course duration
    ended_at = models.DateTimeField()
    # [validation] shall be in the course duration

    # [validation] time intervals shall not overlap each other

    # it may not be necessary
    def __str__(self) -> str:
        return f"{self.teacher_profile}-{self.course}"
