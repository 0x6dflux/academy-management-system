from datetime import date, timedelta
from decimal import Decimal

from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)
from rest_framework.exceptions import ValidationError

from account.models import TeacherProfile, User
from education.models import Course, ReportHistory, Semester, Session
from finance.models import WageRate

USER = User


class WageService:
    semester: Semester
    starting_date: date
    ending_date: date
    sessions: QuerySet

    @classmethod
    def _set_date_range(cls, year: int, month: int) -> None:
        """This method sets the `[starting, ending]` dates."""

        cls.starting_date = date(year, month, 1)
        cls.ending_date = date(year, month + 1, 1) - timedelta(1)

    @classmethod
    def _filter_sessions(cls) -> None:
        """This method filters the sessions in the database."""

        cls.sessions = (
            Session.objects
            # .prefetch_related("report")
            # .select_related("course")
            .filter(
                course__semester=cls.semester,
                date__range=(cls.starting_date, cls.ending_date),
                # date__gte=cls.starting_date,
                # date__lt=cls.ending_date,
            ).annotate(
                latest_report_change=Subquery(
                    ReportHistory.objects.filter(report=OuterRef("report__pk"))
                    .order_by("-modified_at", "-id")
                    .values("change")[:1]
                )
            )
        )

    @classmethod
    def _are_reports_submitted(cls) -> bool:
        """This method checks whether all reports have been submitted or not."""

        return not cls.sessions.filter(report__isnull=True).exists()

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
    def _is_wage_rate_set_for_all_teachers(cls) -> bool:
        return not cls.sessions.filter(
            report__teacher_profile__wage_rate__amount__isnull=True,
        ).exists()

    @classmethod
    def _summer_coefficient(cls) -> Decimal:
        return Decimal("1.1") if cls.semester.is_summer_semester else Decimal("1.0")

    @classmethod
    def _wage_per_teacher(cls) -> QuerySet:
        return (
            cls.sessions.filter(
                latest_report_change=ReportHistory.ChangeChoices.APPROVED
            )
            .exclude(
                report__delay_time__gte=100,
            )
            .annotate(teacher_profile=F("report__teacher_profile"))
            .annotate(
                delay_penalty_coefficient=ExpressionWrapper(
                    1 - F("report__delay_time") / 100,
                    DecimalField(max_digits=11, decimal_places=2),
                )
            )
            .annotate(
                session_length_coefficient=Case(
                    When(
                        course__sessions_length=Course.SessionLengthChoices.MIN60,
                        then=Value(Decimal("0.7")),
                    ),
                    When(
                        course__sessions_length=Course.SessionLengthChoices.MIN90,
                        then=Value(Decimal("1.0")),
                    ),
                    When(
                        course__sessions_length=Course.SessionLengthChoices.MIN120,
                        then=Value(Decimal("1.3")),
                    ),
                )
            )
            .annotate(
                wage_rate=Subquery(
                    WageRate.objects.filter(
                        semester=cls.semester,
                        teacher_profile=OuterRef("report__teacher_profile"),
                    ).values("amount")[:1]
                )
            )
            .annotate(
                wage_per_report=ExpressionWrapper(
                    F("delay_penalty_coefficient")
                    * F("session_length_coefficient")
                    * F("wage_rate")
                    * cls._summer_coefficient(),
                    DecimalField(max_digits=11, decimal_places=2),
                )
            )
            .values("teacher_profile")
            .annotate(wage=Sum("wage_per_report"))
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

        # verify that every session has a submitted report
        if not cls._are_reports_submitted():
            raise ValidationError("There are reports which are not submitted!")

        # checks whether all teachers have wage_rate
        if not cls._is_wage_rate_set_for_all_teachers():
            raise ValidationError("There are teachers without wage rate!")

        # are reports reviewed?
        if not cls._are_reports_reviewed():
            raise ValidationError("There are reports which are not reviewed!")

        # calculate wage for all teachers
        wage_per_teacher = cls._wage_per_teacher()

        # insert into db
