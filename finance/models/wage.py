from django.db import models

from system.models import BaseModel


class Wage(BaseModel):
    class MonthChoices(models.IntegerChoices):
        JAN = 1, "January"
        FEB = 2, "February"
        MAR = 3, "March"
        APR = 4, "April"
        MAY = 5, "May"
        JUN = 6, "June"
        JUL = 7, "July"
        AUG = 8, "August"
        SEP = 9, "September"
        OCT = 10, "October"
        NOV = 11, "November"
        DEC = 12, "December"

    teacher_profile = models.ForeignKey("account.TeacherProfile", models.CASCADE)
    year = models.SmallIntegerField()
    # [validation] shall be greater than the current year
    # this validation is not good, to be able to import previous records
    month = models.SmallIntegerField(choices=MonthChoices.choices)
    calculated_by_system = models.DecimalField(max_digits=11, decimal_places=2)
    # 999_999_999.99
    is_modified = models.BooleanField(default=False)
    modified_by = models.ForeignKey(
        "account.User",
        models.CASCADE,
        null=True,
        blank=True,
    )
    # [validation] if `is_modified==True` then this field is required
    calculated_by_finance_officer = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        null=True,
        blank=True,
    )
    # 999_999_999.99
    # [validation] if `is_modified==True` then this field is required
    # [permission] only users with FIO role
    modification_reason = models.TextField(blank=True)
    # [validation] if `is_modified==True` then this field is required

    def __str__(self) -> str:
        return f"{self.year}-{self.get_month_display()}"  # type: ignore
