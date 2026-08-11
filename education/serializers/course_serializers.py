from rest_framework import serializers

from education.models import Course, Semester
from system.utils import SetUserModifierMixin
from system.validators.name_validators import _name_validator


class CourseModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    semester = serializers.StringRelatedField()  # type: ignore
    semester_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Semester.objects.all(),
        write_only=True,
        source="semester",
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "semester",
            "semester_id",
            "name",
            "level",
            "start_date",
            "end_date",
            "sessions_length",
            "serial_number",
        )
        read_only_fields = ("serial_number",)

    def validate_name(self, value: str) -> str:
        return _name_validator(value)

    def validate(self, data: dict) -> dict:
        # validation data for `POST`, `PUT`, and `PATCH` methods

        if self.instance:
            # `PUT` or `PATCH`
            start_date = data.get("start_date", self.instance.start_date)
            end_date = data.get("end_date", self.instance.end_date)
            semester = data.get("semester", self.instance.semester)
            # [HINT] due to `source="semester"` at line 13, the DRF will set the
            # semester object on `data` with `semester` key.
        else:
            # `POST`
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            semester = data.get("semester")
            # [HINT] due to `source="semester"` at line 13, the DRF will set the
            # semester object on `data` with `semester` key.

        if start_date and end_date and semester:
            if not start_date <= end_date:
                raise serializers.ValidationError(
                    "Course shall not end before start_date!"
                )

            if not semester.start_date <= start_date <= semester.end_date:
                raise serializers.ValidationError(
                    "Course start_date shall be within the semester duration!"
                )

            if not semester.start_date <= end_date <= semester.end_date:
                raise serializers.ValidationError(
                    "Course end_date shall be within the semester duration!"
                )

        return data
