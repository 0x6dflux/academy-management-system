from rest_framework import serializers

from account.models import TeacherProfile
from account.serializers.user_serializer import UserSerializer


class TeacherProfileEducationOfficerRoleSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = "__all__"


class TeacherProfileTeacherRoleSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "user",
            "first_name",
            "last_name",
            "phone_number",
            "emergency_phone_number",
        ]
