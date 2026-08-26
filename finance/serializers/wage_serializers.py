from datetime import date

from django.utils import timezone
from rest_framework import serializers

from finance.models import Wage


class WageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wage
        fields = ("id", "teacher_profile", "year", "month", "amount")
        read_only_fields = ("teacher_profile", "year", "month", "amount")


class WageCalculationSerializer(serializers.Serializer):
    month = serializers.ChoiceField(Wage.MonthChoices.choices, write_only=True)
    year = serializers.IntegerField(write_only=True)

    def validate(self, data: dict) -> dict:
        current_date = timezone.localdate()
        first_day_of_current_month = date(current_date.year, current_date.month, 1)

        requested_date = date(data["year"], data["month"], 1)

        if not requested_date < first_day_of_current_month:
            raise serializers.ValidationError(
                "Wages can only be calculated for completed months!"
            )

        return data
