from django.db import models

from system.models import SoftDeleteBaseModel


class TeacherCourse(SoftDeleteBaseModel):
    """customized through table between Teacher and Course"""

    teacher_profile = models.ForeignKey(
        "account.TeacherProfile",
        models.CASCADE,
        "courses",
    )
    course = models.ForeignKey("education.course", models.CASCADE, "teachers")
    started_at = models.DateField()
    # [validation] shall be in the course duration
    ended_at = models.DateField()
    # [validation] shall be in the course duration

    # [validation] time intervals shall not overlap each other

    # class Meta:
    #     constraints = (
    #         models.UniqueConstraint(
    #             fields=["teacher_profile", "course"],
    #             name="unique_teacher_course",
    #         ),
    #     )

    # it may not be necessary
    def __str__(self) -> str:
        return f"{self.teacher_profile}-{self.course}"
