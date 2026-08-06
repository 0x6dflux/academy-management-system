from rest_framework.serializers import ModelSerializer

from account.models import User

USER = User


class CreateUserSerializer(ModelSerializer):
    class Meta:
        model = USER
        fields = ("email", "password", "role")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data) -> USER:
        return USER.objects.create_user(**validated_data)
        # we want to use the manager to save the user, otherwise,
        # it is required to call the `.set_password()` method
