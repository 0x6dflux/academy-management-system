class SetUserModifierMixin:
    """
    This mixin sets the `created_by` and `updated_by` fields in a serializer.
    """

    # do not define `.create()` and `.update()` methods here.
    # due to `MRO` these methods shall be written in the serializer definition block

    def _set_created_by(self, validated_data: dict) -> dict:
        """Receives user and validated_data in a serializer to set the `created_by` field"""

        validated_data["created_by"] = self.context["request"].user  # type: ignore

        return validated_data

    def _set_updated_by(self, validated_data: dict) -> dict:
        """Receives user and validated_data in a serializer to set the `updated_by` field"""

        validated_data["updated_by"] = self.context["request"].user  # type: ignore

        return validated_data
