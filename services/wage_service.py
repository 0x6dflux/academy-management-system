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

from education.models import Course, ReportHistory, Session
from finance.models import WageRate


class WageService:
    starting_date: date
    ending_date: date
    sessions: QuerySet
    teachers_without_wage: QuerySet

    @classmethod
    def _set_date_range(cls, year: int, month: int) -> None:
        """This method sets the `[starting, ending]` dates."""

        cls.starting_date = date(year, month, 1)

        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        cls.ending_date = date(next_year, next_month, 1) - timedelta(1)

    @classmethod
    def _filter_sessions_in_wage_calculation_duration(cls) -> None:
        """This method filters sessions during the wage calculation period."""

        cls.sessions = cls.sessions.filter(
            date__range=(cls.starting_date, cls.ending_date),
        )

    @classmethod
    def _filter_sessions_against_teachers_not_submitted_all_reports(cls) -> None:
        """
        This method filters sessions without report in the wage calculation period.
        Then extract the responsible teachers assigned to these sessions.
        Finally, the method filters sessions without report and excludes all sessions
        related to the teachers who have not submitted all reports.
        """

        teachers_not_submitted_all_reports = (
            cls.sessions.filter(
                report__isnull=True,
                date__range=(
                    F("course__teachers__started_at"),
                    F("course__teachers__ended_at"),
                ),
            )
            .values_list("course__teachers__teacher_profile", flat=True)
            .distinct()
        )

        cls.sessions = cls.sessions.filter(report__isnull=False).exclude(
            report__teacher_profile__in=teachers_not_submitted_all_reports
        )

        cls.teachers_without_wage = teachers_not_submitted_all_reports

    @classmethod
    def _filter_sessions(cls) -> None:
        """This method applies filters on the sessions queryset."""

        cls._filter_sessions_in_wage_calculation_duration()
        cls._filter_sessions_against_teachers_not_submitted_all_reports()

    @classmethod
    def _annotate_the_latest_report_change(cls) -> None:
        """This method adds a new field on the sessions queryset as `latest_report_change`."""

        cls.sessions = cls.sessions.annotate(
            latest_report_change=Subquery(
                ReportHistory.objects.filter(report=OuterRef("report__pk"))
                .order_by("-modified_at", "-id")
                .values("change")[:1]
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
    def _is_wage_rate_set_for_all_teachers(cls) -> bool:
        """
        This method checks whether the wage rate has been defined for
        all teachers in the wage calculation period.
        """

        return (
            not cls.sessions.annotate(
                wage_rate=Subquery(
                    WageRate.objects.filter(
                        semester=OuterRef("course__semester"),
                        teacher_profile=OuterRef("report__teacher_profile"),
                    ).values("amount")[:1]
                )
            )
            .filter(wage_rate__isnull=True)
            .exists()
        )

    @classmethod
    def _wage_per_teacher(cls) -> QuerySet:
        """This method calculates a teacher wage in the specified month."""

        return (
            cls.sessions.filter(
                latest_report_change=ReportHistory.ChangeChoices.APPROVED
            )
            .exclude(
                report__delay_time__gte=100,
            )
            .annotate(
                teacher_profile=F("report__teacher_profile"),
                delay_penalty_coefficient=ExpressionWrapper(
                    1 - F("report__delay_time") / Decimal("100.0"),
                    # both delay_time and 100 are integers
                    # On PostgreSQL, 50 / 100 becomes 0,
                    # making the coefficient 1 instead of 0.5
                    DecimalField(max_digits=11, decimal_places=2),
                ),
                session_length_coefficient=Case(
                    When(
                        course__sessions_length=Course.SessionLengthChoices.MIN60,
                        then=Value(Decimal("0.7")),
                    ),
                    When(
                        course__sessions_length=Course.SessionLengthChoices.MIN120,
                        then=Value(Decimal("1.3")),
                    ),
                    default=Value(Decimal("1.0")),
                ),
                wage_rate=Subquery(
                    WageRate.objects.filter(
                        semester=OuterRef("course__semester"),
                        teacher_profile=OuterRef("report__teacher_profile"),
                    ).values("amount")[:1]
                ),
                summer_coefficient=Case(
                    When(
                        course__semester__is_summer_semester=True,
                        then=Value(Decimal("1.1")),
                    ),
                    default=Value(Decimal("1.0")),
                ),
                wage_per_report=ExpressionWrapper(
                    F("delay_penalty_coefficient")
                    * F("session_length_coefficient")
                    * F("wage_rate")
                    * F("summer_coefficient"),
                    DecimalField(max_digits=11, decimal_places=2),
                ),
            )
            .values("teacher_profile")
            .annotate(wage=Sum("wage_per_report"))
            .values_list("teacher_profile", "wage")
        )

    @classmethod
    def calculate_wages(cls, year: int, month: int) -> None:
        """
        This method is the entrypoint of this service.
        """

        # resetting the cls.sessions in every run
        cls.sessions = Session.objects.all()

        # set the starting and ending dates
        cls._set_date_range(year, month)

        # filter the sessions
        cls._filter_sessions()

        # annotate the late report change
        cls._annotate_the_latest_report_change()

        # checks whether all teachers have wage_rate
        if not cls._is_wage_rate_set_for_all_teachers():
            raise ValidationError("There are teachers without wage rate!")

        # are reports reviewed?
        if not cls._are_reports_reviewed():
            raise ValidationError("There are reports which are not reviewed!")

        # calculate wage for all teachers
        wage_per_teacher = cls._wage_per_teacher()

        # insert into db
        # for teachers_without_wage consider wage=0
