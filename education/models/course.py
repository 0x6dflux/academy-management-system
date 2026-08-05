from django.db import models

from system.models import BaseModel, SerialNumberAbbreviation


def get_next_serial() -> int:
    last_serial = (
        Course.all_objects.order_by("-pk")
        # it is conventionally better to use `pk` rather than `id`
        .values_list("serial_digit", flat=True)
        .first()
    )

    return last_serial + 1 if last_serial else 1


class Course(BaseModel):
    class SessionLengthChoices(models.IntegerChoices):
        MIN60 = 60, "60 min"
        MIN90 = 90, "90 min"
        MIN120 = 120, "120 min"

    class LevelChoices(models.IntegerChoices):
        BASIC = 0, "Basic"
        INTERMEDIATE = 1, "Intermediate"
        ADVANCED = 2, "Advanced"

    semester = models.ForeignKey("education.Semester", models.CASCADE, "courses")
    name = models.CharField(max_length=50)
    level = models.PositiveSmallIntegerField(choices=LevelChoices)
    start_date = models.DateField()
    # [validation] shall be in semester duration
    end_date = models.DateField()
    # [validation] shall be greater than `Course.start_date`
    # [validation] shall be in semester duration
    sessions_length = models.PositiveSmallIntegerField(choices=SessionLengthChoices)
    serial_digit = models.PositiveSmallIntegerField(
        unique=True,
        default=get_next_serial,
    )

    @property
    def serial_number(self):  # CRXXXX
        return f"{SerialNumberAbbreviation.COURSE}{self.serial_digit:04d}"

    def __str__(self) -> str:
        return self.name
