from rest_framework import serializers

from account.serializers import TeacherProfileTeacherRoleSerializer
from education.models import Course, Semester, TeacherCourse
from system.utils import SetUserModifierMixin


class TeacherCourseModelSerializer(serializers.ModelSerializer):
    teacher = TeacherProfileTeacherRoleSerializer(
        source="teacher_profile",
        read_only=True,
    )

    class Meta:
        model = TeacherCourse
        fields = ("teacher", "started_at", "ended_at")


class CourseModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    school = serializers.CharField(read_only=True, source="semester.school.name")
    semester = serializers.StringRelatedField()  # type: ignore
    semester_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Semester.objects.all(),
        write_only=True,
        source="semester",
    )
    # level = serializers.CharField(read_only=True, source="get_level_display")
    # sessions_length = serializers.CharField(
    #     read_only=True,
    #     source="get_sessions_length_display",
    # )
    teachers = TeacherCourseModelSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "school",
            "semester",
            "semester_id",
            "name",
            "level",
            "start_date",
            "end_date",
            "sessions_length",
            "serial_number",
            "teachers",
        )
        read_only_fields = ("serial_number",)

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

        if not start_date <= end_date:  # type: ignore
            raise serializers.ValidationError("Course shall not end before start_date!")

        if not semester.start_date <= start_date <= semester.end_date:  # type: ignore
            raise serializers.ValidationError(
                "Course start_date shall be within the semester duration!"
            )

        if not semester.start_date <= end_date <= semester.end_date:  # type: ignore
            raise serializers.ValidationError(
                "Course end_date shall be within the semester duration!"
            )

        return data
