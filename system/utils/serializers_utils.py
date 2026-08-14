class SetUserModifierMixin:
    """
    This mixin automatically sets `created_by` and `updated_by`
    by hooking into the DRF serializer create/update flow via MRO.
    """

    def create(self, validated_data: dict):
        if hasattr(self, "context") and "request" in self.context:  # type: ignore
            validated_data["created_by"] = self.context["request"].user  # type: ignore
            validated_data["updated_by"] = self.context["request"].user  # type: ignore

        return super().create(validated_data)  # type: ignore

    def update(self, instance, validated_data: dict):
        if hasattr(self, "context") and "request" in self.context:  # type: ignore
            validated_data["updated_by"] = self.context["request"].user  # type: ignore

        return super().update(instance, validated_data)  # type: ignore
