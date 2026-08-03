from django.db import models

from system.models import BaseModel


class Wage(BaseModel):
    class MonthChoices(models.IntegerChoices):
        MONTH_01 = 1, "January"
        MONTH_02 = 2, "February"
        MONTH_03 = 3, "March"
        MONTH_04 = 4, "April"
        MONTH_05 = 5, "May"
        MONTH_06 = 6, "June"
        MONTH_07 = 7, "July"
        MONTH_08 = 8, "August"
        MONTH_09 = 9, "September"
        MONTH_10 = 10, "October"
        MONTH_11 = 11, "November"
        MONTH_12 = 12, "December"

    teacher_profile = models.ForeignKey(
        "account.TeacherProfile",
        models.CASCADE,
        related_name="wage",
    )
    year = models.SmallIntegerField()
    # [validation] shall be greater than the current year
    # this validation is not good, to be able to import previous records
    month = models.PositiveSmallIntegerField(choices=MonthChoices)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    # 999_999_999.99
    # is_modified = models.BooleanField(default=False)
    # modified_by = models.ForeignKey(
    #     "account.User",
    #     models.CASCADE,
    #     null=True,
    #     blank=True,
    # )
    # # [validation] if `is_modified==True` then this field is required
    # calculated_by_finance_officer = models.DecimalField(
    #     max_digits=11,
    #     decimal_places=2,
    #     null=True,
    #     blank=True,
    # )
    # # 999_999_999.99
    # # [validation] if `is_modified==True` then this field is required
    # # [permission] only users with FIO role
    # modification_reason = models.TextField(blank=True)
    # # [validation] if `is_modified==True` then this field is required

    def __str__(self) -> str:
        return f"{self.year}-{self.month.label}"  # type: ignore
