from django.utils.timezone import now
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
            "id",
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
            teacher_profile = data.get("teacher_profile", self.instance.teacher_profile)
        else:
            # `POST`
            started_at = data.get("started_at")
            ended_at = data.get("ended_at")
            course = data.get("course")
            teacher_profile = data.get("teacher_profile")
            # [HINT] due to `source="course"` at line 19, the DRF will set the
            # course object on `data` with `course` key.

        if self.instance:
            # `PUT` or `PATCH`
            if (
                self.instance.teacher_profile_id != teacher_profile.id  # type: ignore
                and not now().date() < course.start_date  # type: ignore
            ):
                raise serializers.ValidationError(
                    "Changing the teacher during the course is not possible! "
                    "Update the ended_at of the previous teacher and then, "
                    "assign the new teacher to this course."
                )
        else:
            # `POST`
            if TeacherCourse.objects.filter(course=course).exists():  # type: ignore
                raise serializers.ValidationError("This course already has a teacher!")

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
