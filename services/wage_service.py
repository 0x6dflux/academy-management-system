from education.models import Semester


class WageService:
    semester: Semester

    @classmethod
    def calculate_wages(cls, semester: Semester) -> None:
        """
        This method is the entrypoint of this service.
        """

        # set the corresponding semester
        cls.semester = semester

        # set the starting and ending dates

        # filter the sessions

        # are reports reviewed?

        # calculate wage per teacher

        # insert into db
