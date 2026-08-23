from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from finance.models import WageRate
from system.utils import SetUserModifierMixin


class WageRateModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    class Meta:
        model = WageRate
        fields = ("id", "semester", "teacher_profile", "amount")
        validators = (
            UniqueTogetherValidator(
                WageRate.objects.all(),
                ("semester", "teacher_profile"),
            ),
        )
