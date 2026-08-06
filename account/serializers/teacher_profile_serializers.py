from rest_framework import serializers

from account.models import TeacherProfile
from account.serializers.create_user_serializer import CreateUserSerializer
from system.validators import (
    _landline_number_validator,
    _mobile_number_validator,
    _name_validator,
)


class TeacherProfileEducationOfficerRoleSerializer(serializers.ModelSerializer):
    user = CreateUserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = "__all__"


class TeacherProfileTeacherRoleSerializer(serializers.ModelSerializer):
    user = CreateUserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = (
            "user",
            "first_name",
            "last_name",
            "mobile_number",
            "landline_number",
        )

    def validate_first_name(self, value: str) -> str:
        return _name_validator(value)

    def validate_last_name(self, value: str) -> str:
        return _name_validator(value)

    def validate_mobile_number(self, value: str) -> str:
        return _mobile_number_validator(value)

    def validate_landline_number(self, value: str) -> str:
        return _landline_number_validator(value)
