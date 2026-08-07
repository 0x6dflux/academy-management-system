from rest_framework import serializers

from system import enums


def _number_validator(value: str) -> None:
    if not value.isdigit():
        raise serializers.ValidationError("Invalid number!")

    if not 10 <= len(value) <= 15:
        raise serializers.ValidationError("Invalid number length!")


def _country_calling_code_method(value: str) -> None:
    if value not in enums.CountryCallingCodes:
        raise serializers.ValidationError("Invalid country calling code!")


def _mobile_number_prefix_validator(value: str) -> None:
    if value not in enums.MobileNumberPrefixes:
        raise serializers.ValidationError("Invalid mobile number prefix!")


def _landline_number_prefix_validator(value: str) -> None:
    if value not in enums.LandlineNumberPrefixes:
        raise serializers.ValidationError("Invalid landline number prefix!")


def _mobile_number_validator(value: str) -> str:
    _number_validator(value)
    _country_calling_code_method(value[:3])
    _mobile_number_prefix_validator(value[3:6])

    return value


def _landline_number_validator(value: str) -> str:
    _number_validator(value)
    _country_calling_code_method(value[:3])
    _landline_number_prefix_validator(value[3:5])

    return value
