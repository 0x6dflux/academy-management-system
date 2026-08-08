from typing import Any

from account.models import User

USER = User


def _set_created_by(user: USER, validated_data: Any) -> Any:
    """Receives user and validated_data in a serializer to set the `created_by` field"""

    validated_data["created_by"] = user

    return validated_data


def _set_updated_by(user: USER, validated_data: Any) -> Any:
    """Receives user and validated_data in a serializer to set the `updated_by` field"""

    validated_data["updated_by"] = user

    return validated_data
