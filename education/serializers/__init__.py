from education.serializers.course_serializers import CourseModelSerializer
from education.serializers.school_serializers import (
    SchoolContactPersonModelSerializer,
    SchoolModelSerializer,
)
from education.serializers.semester_serializers import SemesterModelSerializer

__all__ = [
    "CourseModelSerializer",
    "SchoolContactPersonModelSerializer",
    "SchoolModelSerializer",
    "SemesterModelSerializer",
]
