from rest_framework import serializers

from education.models import School, Semester
from system.utils import SetUserModifierMixin
from system.validators.name_validators import _name_validator


class SemesterModelSerializer(serializers.ModelSerializer, SetUserModifierMixin):
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

    def create(self, validated_data: dict) -> dict:
        validated_data = self._set_created_by(validated_data)
        validated_data = self._set_updated_by(validated_data)

        return super().create(validated_data)

    def update(self, instance: Semester, validated_data: dict) -> dict:
        validated_data = self._set_updated_by(validated_data)

        return super().update(instance, validated_data)

    def validate_name(self, value: str) -> str:
        return _name_validator(value)
