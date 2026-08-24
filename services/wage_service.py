from datetime import date
from decimal import Decimal

from django.db.models import OuterRef, QuerySet, Subquery
from rest_framework.exceptions import ValidationError

from education.models import ReportHistory, Semester, Session


class WageService:
    semester: Semester
    starting_date: date
    ending_date: date
    sessions: QuerySet

    @classmethod
    def _set_date_range(cls, year: int, month: int) -> None:
        """This method sets the `[starting, ending)` dates."""

        cls.starting_date = date(year, month, 1)
        cls.ending_date = date(year, month + 1, 1)

    @classmethod
    def _filter_sessions(cls) -> None:
        """This method filters the sessions in the database."""

        cls.sessions = (
            Session.objects.prefetch_related("report")
            .select_related("course")
            .filter(
                course__semester=cls.semester,
                date__gte=cls.starting_date,
                date__lt=cls.ending_date,
            )
            .annotate(
                latest_report_change=Subquery(
                    ReportHistory.objects.filter(report=OuterRef("report__pk"))
                    .order_by("-id")
                    .values("change")[:1]
                )
            )
        )

    @classmethod
    def _are_reports_reviewed(cls) -> bool:
        """
        This method checks whether all reports have been reviewed or not.
        If a report latest change is CREATED/UPDATED, it has not been reviewed.
        IF a report latest change is REJECTED, it has been reviewed. The
        corresponding teacher shall update the report to get approval.
        """

        return not cls.sessions.filter(
            latest_report_change__in=(
                ReportHistory.ChangeChoices.CREATED,
                ReportHistory.ChangeChoices.UPDATED,
            )
        ).exists()

    @classmethod
    def _summer_coefficient(cls) -> Decimal:
        return Decimal("1.1") if cls.semester.is_summer_semester else Decimal("1.0")

    @classmethod
    def calculate_wages(cls, semester: Semester, year: int, month: int) -> None:
        """
        This method is the entrypoint of this service.
        """

        # set the corresponding semester
        cls.semester = semester

        # set the starting and ending dates
        cls._set_date_range(year, month)

        # filter the sessions
        cls._filter_sessions()

        # are reports reviewed?
        if not cls._are_reports_reviewed():
            raise ValidationError("There are reports which are not reviewed!")

        # calculate wage per teacher

        # insert into db
