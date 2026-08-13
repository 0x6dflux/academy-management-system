from django.db.models.query import QuerySet
from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import Course
from education.serializers import CourseModelSerializer
from system.utils import SoftDeleteModelViewSetMixin


class CourseFilter(FilterSet):
    school = CharFilter("semester__school__name", "iexact")
    semester = CharFilter("semester__name")
    course = CharFilter("name")
    teacher_first_name = CharFilter("teachers__teacher_profile__first_name")
    teacher_last_name = CharFilter("teachers__teacher_profile__last_name")

    class Meta:
        model = Course
        fields = (
            "school",
            "semester",
            "course",
            "level",
            "sessions_length",
            "teacher_first_name",
            "teacher_last_name",
        )


class CourseModelViewSet(SoftDeleteModelViewSetMixin, ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = Course.objects.all()
    serializer_class = CourseModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = CourseFilter
    search_fields = (
        "semester__school__name",
        "semester__name",
        "name",
        "teachers__teacher_profile__first_name",
        "teachers__teacher_profile__last_name",
    )

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            # .select_related("semester", "semester__school")
            # the above line can be conciser
            .select_related("semester__school")
            .prefetch_related("teachers__teacher_profile")
        )
