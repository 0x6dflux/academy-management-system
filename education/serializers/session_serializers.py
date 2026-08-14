from datetime import datetime

from rest_framework import serializers

from education.models import Course, Session
from system.utils import SetUserModifierMixin


class SessionModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    course = serializers.StringRelatedField()  # type: ignore
    course_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Course.objects.all(),
        write_only=True,
        source="course",
    )

    class Meta:
        model = Session
        fields = (
            "id",
            "course",
            "course_id",
            "date",
            "start_time",
            "end_time",
            "serial_number",
        )
        read_only_fields = ("serial_number",)

    def validate(self, data: dict) -> dict:
        # validation data for `POST`, `PUT`, and `PATCH` methods

        if self.instance:
            # `PUT` or `PATCH`
            date = data.get("date", self.instance.date)
            start_time = datetime.combine(
                date, data.get("start_time", self.instance.start_time)
            )
            end_time = datetime.combine(
                date, data.get("end_time", self.instance.end_time)
            )
            course = data.get("course", self.instance.course)
            # [HINT] due to `source="course"` at line 12, the DRF will set the
            # course object on `data` with `course` key.
        else:
            # `POST`
            date = data.get("date")
            start_time = datetime.combine(date, data.get("start_time"))  # type: ignore
            end_time = datetime.combine(date, data.get("end_time"))  # type: ignore
            course = data.get("course")
            # [HINT] due to `source="course"` at line 13, the DRF will set the
            # course object on `data` with `course` key.

        if not course.start_date <= date <= course.end_date:  # type: ignore
            raise serializers.ValidationError(
                "Session date shall be within the course duration!"
            )

        if (end_time - start_time).seconds != course.sessions_length * 60:  # type: ignore
            raise serializers.ValidationError("Invalid session length!")

        return data
