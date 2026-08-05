from django.db import models

from system.models import BaseModel, SerialNumberAbbreviation


def get_next_serial() -> int:
    last_serial = (
        Session.all_objects.order_by("-pk")
        # it is conventionally better to use `pk` rather than `id`
        .values_list("serial_digit", flat=True)
        .first()
    )

    return last_serial + 1 if last_serial else 1


class Session(BaseModel):
    course = models.ForeignKey("education.Course", models.CASCADE, "sessions")
    date = models.DateTimeField()
    # [validation] shall be in the course duration
    start_time = models.DateTimeField()
    # [validation] `start_time.date()` shall be equal to `date`
    end_time = models.DateTimeField()
    # [validation] `end_time.date()` shall be equal to `date`
    # [validation] `end_time - start_time` shall be equal to `sessions_length`
    serial_digit = models.PositiveSmallIntegerField(
        unique=True,
        default=get_next_serial,
    )

    @property
    def serial_number(self) -> str:  # SSXXXX
        return f"{SerialNumberAbbreviation.SESSION}{self.serial_digit:04d}"

    def __str__(self) -> str:
        return f"{self.date}"
