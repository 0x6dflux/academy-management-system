from rest_framework import serializers


def _name_validator(value: str) -> str:
    if not 0 <= value.count(" ") <= 1:
        raise serializers.ValidationError("Invalid number of spaces in name!")

    if not value.replace(" ", "").isalpha():
        raise serializers.ValidationError("Invalid name!")

    return value
