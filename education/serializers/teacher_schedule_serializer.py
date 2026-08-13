from rest_framework import serializers

from education.models import Course, Session

# class TeacherScheduleReportSerializer


class TeacherScheduleSessionSerializer(serializers.ModelSerializer):
    # [todo] report = TeacherScheduleReportSerializer(read_only=True)
    class Meta:
        model = Session
        fields = ("date", "start_time", "end_time")  # add 'report'
        read_only_fields = ("date", "start_time", "end_time")


class TeacherScheduleCourseSerializer(serializers.ModelSerializer):
    level = serializers.CharField(read_only=True, source="get_level_display")
    sessions_length = serializers.CharField(
        read_only=True,
        source="get_sessions_length_display",
    )
    sessions = TeacherScheduleSessionSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "name",
            "level",
            "start_date",
            "end_date",
            "sessions_length",
            "sessions",
        )
        read_only_fields = ("name", "start_date", "end_date")
