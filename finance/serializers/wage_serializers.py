from rest_framework import serializers

from finance.models import Wage


class WageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wage
        fields = ("id", "teacher_profile", "year", "month", "amount")
        read_only_fields = ("teacher_profile", "year", "month", "amount")
