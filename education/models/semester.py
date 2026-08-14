from django.db import models

from system.models import SerialNumberAbbreviation, SoftDeleteBaseModel


def get_next_serial() -> int:
    last_serial = (
        Semester.all_objects.order_by("-pk")
        # it is conventionally better to use `pk` rather than `id`
        .values_list("serial_digit", flat=True)
        .first()
    )

    return last_serial + 1 if last_serial else 1


class Semester(SoftDeleteBaseModel):
    school = models.ForeignKey("education.School", models.CASCADE, "semesters")
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    # example: 2026-08-04 `00:00:00`
    end_date = models.DateField()
    # example: 2026-08-05 `23:59:59`
    is_summer_semester = models.BooleanField(default=False)
    serial_digit = models.PositiveSmallIntegerField(
        unique=True,
        default=get_next_serial,
    )

    @property
    def serial_number(self) -> str:  # SMXXXX
        return f"{SerialNumberAbbreviation.SEMESTER}{self.serial_digit:04d}"

    def __str__(self) -> str:
        return self.name
