class SoftDeleteModelViewSetMixin:
    def perform_destroy(self, instance):
        instance.soft_delete(updated_by=self.request.user)  # type: ignore
