from rest_framework import serializers

from account.models import TeacherProfile
from education.models import Course, TeacherCourse
from system.utils import SetUserModifierMixin


class TeacherCourseModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    teacher_profile = serializers.StringRelatedField()  # type: ignore
    teacher_profile_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=TeacherProfile.objects.all(),
        write_only=True,
        source="teacher_profile",
    )
    course = serializers.StringRelatedField()  # type: ignore
    course_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=Course.objects.all(),
        write_only=True,
        source="course",
    )

    class Meta:
        model = TeacherCourse
        fields = (
            "pk",
            "teacher_profile",
            "teacher_profile_id",
            "course",
            "course_id",
            "started_at",
            "ended_at",
        )

    def validate(self, data: dict) -> dict:
        # validation data for `POST`, `PUT`, and `PATCH` methods

        if self.instance:
            # `PUT` or `PATCH`
            started_at = data.get("started_at", self.instance.started_at)
            ended_at = data.get("ended_at", self.instance.ended_at)
            course = data.get("course", self.instance.course)
            # [HINT] due to `source="course"` at line 19, the DRF will set the
            # course object on `data` with `course` key.
        else:
            # `POST`
            started_at = data.get("started_at")
            ended_at = data.get("ended_at")
            course = data.get("course")
            # [HINT] due to `source="course"` at line 19, the DRF will set the
            # course object on `data` with `course` key.

        if not started_at < ended_at:  # type: ignore
            raise serializers.ValidationError(
                "A teacher contract shall be at least one-day long!"
            )

        if not course.start_date <= started_at <= course.end_date:  # type: ignore
            raise serializers.ValidationError(
                "A teacher shall start their job within the course duration!"
            )

        if not course.start_date <= ended_at <= course.end_date:  # type: ignore
            raise serializers.ValidationError(
                "A teacher shall end their job within the course duration!"
            )

        return data
