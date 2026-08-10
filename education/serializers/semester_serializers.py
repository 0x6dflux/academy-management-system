from rest_framework import serializers

from education.models import School, Semester
from system.utils import SetUserModifierMixin
from system.validators.name_validators import _name_validator


class SemesterModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    school = serializers.StringRelatedField()  # type: ignore
    school_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=School.objects.all(),
        write_only=True,
        source="school",
    )

    class Meta:
        model = Semester
        fields = (
            "id",
            "school",
            "school_id",
            "name",
            "start_date",
            "end_date",
            "is_summer_semester",
            "serial_number",
        )
        read_only_fields = ("serial_number",)

    def validate_name(self, value: str) -> str:
        return _name_validator(value)
