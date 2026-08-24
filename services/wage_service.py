from datetime import date

from django.db.models import OuterRef, QuerySet, Subquery

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
        )

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

        # calculate wage per teacher

        # insert into db
