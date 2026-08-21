from rest_framework import serializers

from education.models import Course, Report, Session


class TeacherScheduleReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ("is_delayed", "delay_time", "is_approved")


class TeacherScheduleSessionSerializer(serializers.ModelSerializer):
    report = TeacherScheduleReportSerializer(read_only=True)

    class Meta:
        model = Session
        fields = ("date", "start_time", "end_time", "report")
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


class TeacherReportStatQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
    )


class TeacherReportStatSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    period_in_days = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    not_submitted = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    rejected = serializers.IntegerField()
    approved = serializers.IntegerField()
