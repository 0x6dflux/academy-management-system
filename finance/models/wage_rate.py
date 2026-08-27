from django.db import models

from system.models import SoftDeleteBaseModel


class WageRate(SoftDeleteBaseModel):
    # not considering the `related_name` may be a good option
    semester = models.ForeignKey("education.Semester", models.CASCADE, "wage_rate")
    teacher_profile = models.ForeignKey(
        "account.TeacherProfile",
        models.CASCADE,
        "wage_rate",
    )
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    # 999_999_999.99

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("semester", "teacher_profile"),
                condition=models.Q(is_deleted=False),
                name="unique_active_teacher_semester_wage_rate",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="wage_rate_amount_positive",
            ),
        )

    def __str__(self) -> str:
        return f"{self.teacher_profile}-{self.semester}"
