from rest_framework import serializers


def _name_validator(value: str) -> str:
    if not value.isalpha():
        raise serializers.ValidationError("Invalid name!")

    return value
