from datetime import datetime, timedelta

import pytz
from rest_framework import serializers

from config.settings import TIME_ZONE
from education.models import Report, ReportHistory, Session
from system.utils import SetUserModifierMixin


class ReportReadOnlyModelSerializer(serializers.ModelSerializer):
    session = serializers.StringRelatedField()  # type: ignore
    latest_rejection_description = serializers.CharField(
        read_only=True,
        source="rej_desc",
    )

    class Meta:
        model = Report
        fields = (
            "id",
            "session",
            "tutorial_summary",
            "number_of_attendees",
            "number_of_absentees",
            "is_delayed",
            "delay_time",
            "is_approved",
            "latest_rejection_description",
        )
        read_only_fields = (
            "tutorial_summary",
            "number_of_attendees",
            "number_of_absentees",
            "is_delayed",
            "delay_time",
            "is_approved",
        )


class ReportSubmissionWriteOnlyModelSerializer(
    SetUserModifierMixin,
    serializers.ModelSerializer,
):
    session_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Session.objects.all(),
        write_only=True,
        source="session",
    )

    class Meta:
        model = Report
        fields = (
            "id",
            "session_id",
            "tutorial_summary",
            "number_of_attendees",
            "number_of_absentees",
        )
        extra_kwargs = {
            "tutorial_summary": {"write_only": True},
            "number_of_attendees": {"write_only": True},
            "number_of_absentees": {"write_only": True},
        }

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

        if local_now <= local_submission_due_datetime:
            return False, 0

        return True, int(
            (local_now - local_submission_due_datetime).total_seconds()
        ) // 3600

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
                "This report cannot be updated once it is under review or has been approved."
            )


class ReportEDORoleModelSerializer(serializers.ModelSerializer):
    """This serializer is for reading mode."""

    report = ReportTCHRoleModelSerializer(read_only=True)
    report_id = serializers.PrimaryKeyRelatedField(
        queryset=Report.objects.all(),
        write_only=True,
        source="report",
    )
    change = serializers.CharField(
        read_only=True,
        source="get_change_display",
        label="Latest Status",
    )
    is_approved = serializers.BooleanField(write_only=True)
    description = serializers.CharField(allow_blank=True)

    class Meta:
        model = ReportHistory
        fields = (
            # "id",  # to not allow updating
            "report",
            "report_id",
            "change",
            "is_approved",
            "description",
        )

    def validate(self, data: dict) -> dict:
        if data["is_approved"] == False and data["description"] is None:
            raise serializers.ValidationError(
                "Description shall not be blank if the report is not approved."
            )

        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data["role"] = self.context["request"].user.role

        is_report_approved = validated_data.pop("is_approved")
        if is_report_approved:
            validated_data["change"] = ReportHistory.ChangeChoices.APPROVED
        else:
            validated_data["change"] = ReportHistory.ChangeChoices.REJECTED

        return super().create(validated_data)
