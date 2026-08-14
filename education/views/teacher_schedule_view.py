from django.db.models.query import QuerySet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from account.models import User
from account.permissions import IsTeacherOrAdmin
from education.models import Course
from education.serializers import TeacherScheduleCourseSerializer

USER = User


class TeacherScheduleAPIView(ListAPIView):
    http_method_names = ("get",)
    queryset = Course.objects.all()
    serializer_class = TeacherScheduleCourseSerializer
    permission_classes = (IsAuthenticated, IsTeacherOrAdmin)

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset().prefetch_related("sessions")

        if self.request.user.role == USER.RoleChoices.ADMIN:  # type: ignore
            # admin can see all courses and sessions
            return qs

        return qs.filter(teachers__teacher_profile__user=self.request.user)
