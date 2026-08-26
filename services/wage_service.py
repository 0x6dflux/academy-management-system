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
from education.models import Course, ReportHistory, Session
from finance.models import Wage, WageRate

USER = User


class WageService:
    """Instantiate this service and call `calculate_wages()`."""

    def __init__(self, year: int, month: int, user: USER) -> None:
        self.year = year
        self.month = month
        self.user = user

        # set the overall sessions
        self.sessions = Session.objects.all()

        # set the starting and ending dates
        self._set_date_range()

    def _set_date_range(self) -> None:
        """This method sets the `[starting, ending]` dates."""

        self.starting_date = date(self.year, self.month, 1)

        if self.month == 12:
            next_year = self.year + 1
            next_month = 1
        else:
            next_year = self.year
            next_month = self.month + 1

        self.ending_date = date(next_year, next_month, 1) - timedelta(1)

    def _filter_sessions_in_wage_calculation_duration(self) -> None:
        """This method filters sessions during the wage calculation period."""

        self.sessions = self.sessions.filter(
            date__range=(self.starting_date, self.ending_date)
        )

    def _filter_sessions_against_teachers_not_submitted_all_reports(self) -> None:
        """
        This method filters sessions without report in the wage calculation period.
        Then extract the responsible teachers assigned to these sessions.
        Finally, the method filters sessions without report and excludes all sessions
        related to the teachers who have not submitted all reports.
        """

        teachers_not_submitted_all_reports = (
            self.sessions.filter(
                report__isnull=True,
                date__range=(
                    F("course__teachers__started_at"),
                    F("course__teachers__ended_at"),
                ),
            )
            .values_list("course__teachers__teacher_profile", flat=True)
            .distinct()
        )

        self.sessions = self.sessions.filter(report__isnull=False).exclude(
            report__teacher_profile__in=teachers_not_submitted_all_reports
        )

    def _filter_sessions(self) -> None:
        """This method applies filters on the sessions queryset."""

        self._filter_sessions_in_wage_calculation_duration()
        self._filter_sessions_against_teachers_not_submitted_all_reports()

    def _annotate_the_latest_report_change(self) -> None:
        """This method adds a new field on the sessions queryset as `latest_report_change`."""

        self.sessions = self.sessions.annotate(
            latest_report_change=Subquery(
                ReportHistory.objects.filter(report=OuterRef("report__pk"))
                .order_by("-modified_at", "-id")
                .values("change")[:1]
            )
        )

    def _are_reports_reviewed(self) -> bool:
        """
        This method checks whether all reports have been reviewed or not.
        If a report latest change is CREATED/UPDATED, it has not been reviewed.
        IF a report latest change is REJECTED, it has been reviewed. The
        corresponding teacher shall update the report to get approval.
        """

        return not self.sessions.filter(
            latest_report_change__in=(
                ReportHistory.ChangeChoices.CREATED,
                ReportHistory.ChangeChoices.UPDATED,
            )
        ).exists()

    def _is_wage_rate_set_for_all_teachers(self) -> bool:
        """
        This method checks whether the wage rate has been defined for
        all teachers in the wage calculation period.
        """

        return (
            not self.sessions.annotate(
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

    def _wage_per_teacher(self) -> QuerySet:
        """This method calculates a teacher wage in the specified month."""

        return (
            self.sessions.filter(
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

    def _insert_wages_into_db(self) -> None:
        wages = []
        teacher_profile_ids = []
        for teacher_profile_id, wage in self.wage_per_teacher:
            wages.append(
                Wage(
                    teacher_profile_id=teacher_profile_id,
                    year=self.year,
                    month=self.month,
                    amount=wage,
                    created_by=self.user,
                    updated_by=self.user,
                )
            )

            teacher_profile_ids.append(teacher_profile_id)

        wages.extend(
            Wage(
                teacher_profile_id=teacher_profile_id,
                year=self.year,
                month=self.month,
                amount=Decimal("0.0"),
                created_by=self.user,
                updated_by=self.user,
            )
            for teacher_profile_id in TeacherProfile.objects.exclude(
                id__in=teacher_profile_ids
            ).values_list("id", flat=True)
        )

        Wage.objects.bulk_create(
            wages,
            update_conflicts=True,
            update_fields=("amount", "updated_by", "updated_at"),
            unique_fields=("teacher_profile", "year", "month"),
        )

    def calculate_wages(self) -> None:
        """
        This method is the entrypoint of this service.
        """

        # filter the sessions
        self._filter_sessions()

        # annotate the late report change
        self._annotate_the_latest_report_change()

        # checks whether all teachers have wage_rate
        if not self._is_wage_rate_set_for_all_teachers():
            raise ValidationError("There are teachers without wage rate!")

        # are reports reviewed?
        if not self._are_reports_reviewed():
            raise ValidationError("There are reports which are not reviewed!")

        # calculate wage for all teachers
        self.wage_per_teacher = self._wage_per_teacher()

        # insert into db
        self._insert_wages_into_db()
