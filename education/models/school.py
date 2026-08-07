from django.db import models

from system.models import SerialNumberAbbreviation, SoftDeleteBaseModel


# what about concurrency?!
# i ignored it intentionally now and will be implemented in a suitable time =)
def get_next_serial() -> int:
    last_serial = (
        School.all_objects.order_by("-pk")
        # it is conventionally better to use `pk` rather than `id`
        .values_list("serial_digit", flat=True)
        .first()
    )

    return last_serial + 1 if last_serial else 1


class School(SoftDeleteBaseModel):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    landline_number = models.CharField(max_length=15)

    serial_digit = models.PositiveSmallIntegerField(
        unique=True,
        default=get_next_serial,
    )
    # serial_number = models.CharField(max_length=6, default=set_serial_number)  # SCxxxx
    # working with numbers are easier
    # does not parsing from str to int
    # does not limit the db due to presentation
    # instead, a property is defined to present the serial_number

    @property
    def serial_number(self) -> str:  # SCXXXX
        return f"{SerialNumberAbbreviation.SCHOOL}{self.serial_digit:04d}"

    def __str__(self) -> str:
        return self.name


# [DOCUMENTATION]
# def set_serial_number():
#     next_digit = 1

#     # if (all_objects := School.objects.all()).exists():
#     #     next_digit = int(all_objects.last().strip().replace("SC", "")) + 1
#     # the expression will query the db twice:
#     #   1. for .exists() `SELECT 1 FROM school LIMIT 1;`
#     #   2. for .last() `SELECT * FROM school ORDER BY ... DESC LIMIT 1;`
#     # these two queries can be reduced to below if statement
#     # if last_obj := School.objects.last():
#     #     next_digit = int(last_obj.serial_number.strip().replace("SC", "")) + 1
#     # the equivalent query for `School.objects.last()` is
#     # SELECT
#     # id,
#     # name,
#     # email,
#     # landline_number,
#     # serial_number,
#     # created_at,
#     # updated_at,
#     # ...
#     # FROM school
#     # ORDER BY id DESC
#     # LIMIT 1;
#     # but, only the serial_number column is required!!
#     # remember to use all_objects manager to get the latest serial_number,
#     # some may be soft deleted!
#     # last_serial = School.all_objects.values_list("serial_number", flat=True).last()
#     # SELECT serial_number
#     # FROM school
#     # ORDER BY id DESC
#     # LIMIT 1;
#     # [IMPORTANT] `.last()` uses the ordering in the class Meta
#     # consider the below model
#     # class School(BaseModel):
#     #     class Meta:
#     #         ordering = ["created_at"]
#     # then, `School.objects.last()` is not based on the latest `pk`!!
#     last_serial = (
#         School.all_objects.order_by("-id")
#         .values_list("serial_number", flat=True)
#         .first()
#     )

#     if last_serial:
#         next_digit = int(last_serial[2:]) + 1

#     return f"SC{next_digit:04d}"
