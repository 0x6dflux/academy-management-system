from datetime import timedelta

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from account.permissions import IsEducationOfficerOrAdmin
from education.serializers import (
    SubstituteTeacherSerializer,
    TeacherCourseModelSerializer,
)


class SubstituteTeacherAPIView(APIView):
    http_method_names = ("post",)
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    @transaction.atomic
    def post(self, request: Request) -> Response:
        substitute_serializer = SubstituteTeacherSerializer(data=request.data)

        substitute_serializer.is_valid(raise_exception=True)

        session = substitute_serializer.validated_data["session"]
        substitute_teacher = substitute_serializer.validated_data["teacher_profile"]
        original_assignment = substitute_serializer.validated_data[
            "original_assignment"
        ]

        substitution_date = session.date

        old_started_at = original_assignment.started_at
        old_ended_at = original_assignment.ended_at
        original_teacher = original_assignment.teacher_profile
        course = original_assignment.course

        # original teacher - before substitute day
        if old_started_at < substitution_date:
            original_assignment_serializer = TeacherCourseModelSerializer(
                original_assignment,
                data={
                    "ended_at": substitution_date - timedelta(days=1),
                },
                partial=True,
                context={"request": request},
            )

            original_assignment_serializer.is_valid(raise_exception=True)
            original_assignment_serializer.save()
        else:
            # if the substitution date is at beginning
            # the original teacher shall be soft deleted
            # to not to conflict with the rest of code
            original_assignment.soft_delete(request.user)

        # original teacher - after substitute day
        if substitution_date < old_ended_at:
            reassignment_serializer = TeacherCourseModelSerializer(
                data={
                    "teacher_profile_id": original_teacher.id,
                    "course_id": course.id,
                    "started_at": substitution_date + timedelta(days=1),
                    "ended_at": old_ended_at,
                },
                context={"request": request},
            )

            reassignment_serializer.is_valid(raise_exception=True)
            reassignment_serializer.save()

        # substitute teacher - the session date
        substitute_assignment_serializer = TeacherCourseModelSerializer(
            data={
                "teacher_profile_id": substitute_teacher.id,
                "course_id": course.id,
                "started_at": substitution_date,
                "ended_at": substitution_date,
            },
            context={"request": request},
        )

        substitute_assignment_serializer.is_valid(raise_exception=True)
        substitute_assignment_serializer.save()

        return Response(
            substitute_assignment_serializer.data,
            status=HTTP_201_CREATED,
        )
