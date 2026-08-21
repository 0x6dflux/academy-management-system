from rest_framework import serializers

from education.models import School, Semester
from system.utils import SetUserModifierMixin


class SemesterModelSerializer(SetUserModifierMixin, serializers.ModelSerializer):
    school = serializers.StringRelatedField()  # type: ignore
    school_id = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=School.objects.all(),
        write_only=True,
        source="school",
    )

    class Meta:
        model = Semester
        fields = (
            "id",
            "school",
            "school_id",
            "name",
            "start_date",
            "end_date",
            "is_summer_semester",
            "serial_number",
        )
        read_only_fields = ("serial_number",)

    def validate(self, data: dict) -> dict:
        # validation data for `POST`, `PUT`, and `PATCH` methods

        if self.instance:
            # `PUT` or `PATCH`
            start_date = data.get("start_date", self.instance.start_date)
            end_date = data.get("end_date", self.instance.end_date)
            school = data.get("school", self.instance.school)
            # [HINT] due to `source="school"` at line 14, the DRF will set the
            # school object on `data` with `school` key.
        else:
            # `POST`
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            school = data.get("school")

        if not start_date < end_date:  # type: ignore
            raise serializers.ValidationError(
                "Semester shall not end before start_date!"
            )

        previous_semesters = (
            Semester.objects.filter(school=school)
            .exclude(end_date__lt=start_date)
            .exclude(start_date__gt=end_date)
        )

        if self.instance:
            # [IMPORTANT]
            # QuerySet methods return a new QuerySet instead of modifying the original. or
            # QuerySet methods like filter() and exclude() do not modify the
            # original QuerySet; they return a new QuerySet, so the result must
            # be reassigned if we want to apply the change.
            previous_semesters = previous_semesters.exclude(id=self.instance.id)

        if previous_semesters.exists():
            raise serializers.ValidationError(
                "Semester shall not overlap with previous semesters!"
            )

        return data
