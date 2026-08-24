from datetime import date

from education.models import Semester


class WageService:
    semester: Semester
    starting_date: date
    ending_date: date

    @classmethod
    def _set_date_range(cls, year: int, month: int) -> None:
        """This method sets the `[starting, ending)` dates."""

        cls.starting_date = date(year, month, 1)
        cls.ending_date = date(year, month + 1, 1)

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

        # are reports reviewed?

        # calculate wage per teacher

        # insert into db
