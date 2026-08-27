from rest_framework import serializers

from account.models import TeacherProfile
from education.models import Session, TeacherCourse


class SubstituteTeacherSerializer(serializers.Serializer):
    session = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all())  # type: ignore
    teacher_profile = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=TeacherProfile.objects.all()
    )

    def validate(self, data: dict) -> dict:
        session = data["session"]
        substitute_teacher = data["teacher_profile"]

        original_assignment = TeacherCourse.objects.filter(
            course=session.course,
            started_at__lte=session.date,
            ended_at__gte=session.date,
        ).first()

        if original_assignment is None:
            raise serializers.ValidationError(
                "This course has no teacher assigned on this date!"
            )

        if original_assignment.teacher_profile == substitute_teacher:
            raise serializers.ValidationError(
                "The substitute teacher cannot be the current teacher!"
            )

        if hasattr(session, "report"):
            raise serializers.ValidationError(
                "A substitute teacher cannot be assigned after a report has been submitted!"
            )

        data["original_assignment"] = original_assignment

        return data
