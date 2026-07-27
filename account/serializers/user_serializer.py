from typing import Any

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

USER = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = USER
        fields = ["username", "password", "role", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data) -> USER:  # type: ignore
        return USER.objects.create_user(**validated_data)
