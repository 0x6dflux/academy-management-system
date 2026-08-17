from django.db import models

from account.models import User
from education.models.report_history import ReportHistory
from system.models import BaseModel, SerialNumberAbbreviation

USER = User


def get_next_serial() -> int:
    last_serial = (
        # as per project requirements, the `Report` model shall not be
        # soft or hard deleted. so, the default manager shall be used.
        Report.objects.order_by("-pk")
        # it is conventionally better to use `pk` rather than `id`
        .values_list("serial_digit", flat=True)
        .first()
    )

    return last_serial + 1 if last_serial else 1


class Report(BaseModel):
    session = models.OneToOneField(
        "education.Session",
        models.SET_NULL,
        related_name="report",
        null=True,
        blank=True,
    )
    teacher_profile = models.ForeignKey(
        "account.TeacherProfile",
        models.SET_NULL,
        "reports",
        null=True,
        blank=True,
    )
    tutorial_summary = models.TextField()
    number_of_attendees = models.PositiveSmallIntegerField()
    number_of_absentees = models.PositiveSmallIntegerField()
    is_delayed = models.BooleanField()
    delay_time = models.PositiveSmallIntegerField()
    serial_digit = models.PositiveSmallIntegerField(
        unique=True,
        default=get_next_serial,
    )

    @property
    def is_approved(self) -> bool:
        return (
            self.histories.last().change == ReportHistory.ChangeChoices.APPROVED  # type: ignore
            and self.histories.last().role == USER.RoleChoices.EDUCATION_OFFICER  # type: ignore
            # the above condition is only for double-checking
        )

    @property
    def can_TCH_update(self) -> bool:
        return (
            self.histories.last().change == ReportHistory.ChangeChoices.REJECTED  # type: ignore
            and self.histories.last().role == USER.RoleChoices.EDUCATION_OFFICER  # type: ignore
            # the above condition is only for double-checking
        )

    @property
    def rej_desc(self) -> str:
        """This property returns the latest rejection description."""

        return (
            self.histories.filter(change=ReportHistory.ChangeChoices.REJECTED)  # type: ignore
            .last()
            .description  # type: ignore
        )

    @property
    def serial_number(self) -> str:  # RPXXXX
        return f"{SerialNumberAbbreviation.REPORT}{self.serial_digit:04d}"

    def __str__(self) -> str:
        return f"{self.serial_number}"

    class SoftDeletionOptions:
        cascade = False
