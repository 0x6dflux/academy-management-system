from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

if TYPE_CHECKING:
    from account.models import User

USER: User = get_user_model()  # type: ignore


class UserSerializer(ModelSerializer):
    class Meta:
        model = USER
        fields = ["username", "password", "role", "email"]
        # write_only_fields = ["password"]
        # the above line is incorrect
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data) -> USER:  # type: ignore
        return USER.objects.create_user(**validated_data)
        # we want to use the manager to save the user, otherwise,
        # it is required to call the `.set_password()` method
