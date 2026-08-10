from rest_framework import serializers

from education.models import School, SchoolContactPerson
from system.utils import SetUserModifierMixin
from system.validators import (
    _landline_number_validator,
    _mobile_number_validator,
    _name_validator,
)


class SchoolContactPersonModelSerializer(
    SetUserModifierMixin,
    serializers.ModelSerializer,
):
    school = serializers.StringRelatedField()  # type: ignore
    school_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=School.objects.all(),
        write_only=True,
        source="school",
    )

    class Meta:
        model = SchoolContactPerson
        fields = (
            "id",
            "first_name",
            "last_name",
            "school_role",
            "mobile_number",
            "landline_extension_number",
            "school",
            "school_id",
        )

    def validate_first_name(self, value: str) -> str:
        return _name_validator(value)

    def validate_last_name(self, value: str) -> str:
        return _name_validator(value)

    def validate_mobile_number(self, value: str) -> str:
        return _mobile_number_validator(value)


class SchoolModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    contact_people = serializers.StringRelatedField(many=True, read_only=True)  # type: ignore

    class Meta:
        model = School
        fields = (
            "id",
            "name",
            "email",
            "landline_number",
            "serial_number",
            "contact_people",
        )
        read_only_fields = ("serial_number",)

    def validate_name(self, value: str) -> str:
        return _name_validator(value)

    def validate_landline_number(self, value: str) -> str:
        return _landline_number_validator(value)
