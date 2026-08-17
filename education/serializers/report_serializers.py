from datetime import datetime, timedelta

import pytz
from rest_framework import serializers

# from account.models import TeacherProfile
from config.settings import TIME_ZONE
from education.models import Report, Session
from system.utils import SetUserModifierMixin


class ReportTCHRoleModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    session = serializers.StringRelatedField()  # type: ignore
    session_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Session.objects.all(),
        write_only=True,
        source="session",
    )
    # teacher_profile = serializers.StringRelatedField()  # type: ignore
    # teacher_profile_id = serializers.PrimaryKeyRelatedField(  # type: ignore
    #     queryset=TeacherProfile.objects.all(),
    #     write_only=True,
    #     source="teacher_profile",
    # )

    class Meta:
        model = Report
        fields = (
            "id",
            "session",
            "session_id",
            # "teacher_profile",
            # "teacher_profile_id",
            "tutorial_summary",
            "number_of_attendees",
            "number_of_absentees",
            "is_delayed",
            "delay_time",
            "is_approved",
            "rej_desc",
        )
        read_only_fields = (
            "is_delayed",
            "delay_time",
            "is_approved",
            "rej_desc",
        )

    @staticmethod
    def delay_calculation(session) -> tuple[bool, int]:
        """
        This method determines whether the report is submitted with delay or not as a boolean variable.
        Moreover, this method calculates the delay time in rounded down hours.
        """

        submission_due_datetime = datetime.combine(
            session.date, session.end_time
        ) + timedelta(hours=48)

        tz = pytz.timezone(TIME_ZONE)
        local_submission_due_datetime = tz.localize(submission_due_datetime)
        local_now = datetime.now(tz)

        if local_now > local_submission_due_datetime:
            return True, (local_now - local_submission_due_datetime).seconds // 3600

        return False, 0

    def create(self, validated_data: dict):

        validated_data["teacher_profile"] = self.context["request"].user.profile

        session = validated_data["session"]
        validated_data["is_delayed"], validated_data["delay_time"] = (
            self.delay_calculation(session)
        )

        return super().create(validated_data)

    def update(self, instance, validated_data: dict):
        if instance.can_TCH_update:
            session = validated_data["session"] or instance.session

            validated_data["is_delayed"], validated_data["delay_time"] = (
                self.delay_calculation(session)
            )

            return super().update(instance, validated_data)
        else:
            raise serializers.ValidationError(
                "This report cannot be updated while it is pending review by the education officer."
            )
