from datetime import date, time
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from account.models import TeacherProfile, User
from education.models import (
    Course,
    Report,
    ReportHistory,
    School,
    Semester,
    Session,
    TeacherCourse,
)
from finance.models import Wage, WageRate
from services.wage_service import WageService


class WageServiceBehaviorTestCase(TestCase):
    calculation_year = 2026
    calculation_month = 1

    def setUp(self) -> None:
        self.admin = User.objects.create_user(
            "service-admin@example.com",
            "admin-password",
            role=User.RoleChoices.ADMIN,
        )
        self.finance_officer = User.objects.create_user(
            "service-fio@example.com",
            "finance-password",
            role=User.RoleChoices.FINANCE_OFFICER,
        )
        self.education_officer = User.objects.create_user(
            "service-edo@example.com",
            "education-password",
            role=User.RoleChoices.EDUCATION_OFFICER,
        )
        self.teacher = User.objects.create_user(
            "service-teacher@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        self.teacher_profile = self.create_teacher_profile(
            self.teacher,
            first_name="Service",
            last_name="Teacher",
        )
        self.school = School.objects.create(
            name="Service Test School",
            email="service-school@example.com",
            landline_number="02140000001",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.semester = self.create_semester(
            name="January 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    def create_teacher_profile(
        self,
        user: User,
        *,
        first_name: str,
        last_name: str,
    ) -> TeacherProfile:
        return TeacherProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            mobile_number=f"0912{user.pk:07d}",
            landline_number=f"0214{user.pk:07d}",
            created_by=self.admin,
            updated_by=self.admin,
        )

    def create_semester(
        self,
        *,
        name: str,
        start_date: date,
        end_date: date,
        is_summer: bool = False,
    ) -> Semester:
        return Semester.objects.create(
            school=self.school,
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_summer_semester=is_summer,
            created_by=self.admin,
            updated_by=self.admin,
        )

    def create_rate(
        self,
        *,
        semester: Semester | None = None,
        teacher_profile: TeacherProfile | None = None,
        amount: Decimal = Decimal("200000.00"),
    ) -> WageRate:
        return WageRate.objects.create(
            semester=semester or self.semester,
            teacher_profile=teacher_profile or self.teacher_profile,
            amount=amount,
            created_by=self.finance_officer,
            updated_by=self.finance_officer,
        )

    def create_course(
        self,
        *,
        name: str = "Service Test Course",
        semester: Semester | None = None,
        teacher_profile: TeacherProfile | None = None,
        session_length: int = Course.SessionLengthChoices.MIN90,
        started_at: date | None = None,
        ended_at: date | None = None,
    ) -> Course:
        semester = semester or self.semester
        teacher_profile = teacher_profile or self.teacher_profile
        course = Course.objects.create(
            semester=semester,
            name=name,
            level=Course.LevelChoices.BASIC,
            start_date=semester.start_date,
            end_date=semester.end_date,
            sessions_length=session_length,
            created_by=self.admin,
            updated_by=self.admin,
        )
        TeacherCourse.objects.create(
            teacher_profile=teacher_profile,
            course=course,
            started_at=started_at or course.start_date,
            ended_at=ended_at or course.end_date,
            created_by=self.admin,
            updated_by=self.admin,
        )
        return course

    def create_session(
        self,
        *,
        course: Course,
        session_date: date,
    ) -> Session:
        end_times: dict[int, time] = {
            Course.SessionLengthChoices.MIN60: time(10, 0),
            Course.SessionLengthChoices.MIN90: time(10, 30),
            Course.SessionLengthChoices.MIN120: time(11, 0),
        }
        return Session.objects.create(
            course=course,
            date=session_date,
            start_time=time(9, 0),
            end_time=end_times[course.sessions_length],
            created_by=self.admin,
            updated_by=self.admin,
        )

    def create_report(
        self,
        *,
        session: Session,
        teacher_profile: TeacherProfile | None = None,
        delay_time: int = 0,
        changes: tuple[int, ...] = (ReportHistory.ChangeChoices.APPROVED,),
    ) -> Report:
        teacher_profile = teacher_profile or self.teacher_profile
        report = Report.objects.create(
            session=session,
            teacher_profile=teacher_profile,
            tutorial_summary="Service behavior test report",
            number_of_attendees=10,
            number_of_absentees=0,
            is_delayed=delay_time > 0,
            delay_time=delay_time,
            created_by=teacher_profile.user,
            updated_by=teacher_profile.user,
        )
        for change in changes:
            reviewer = (
                teacher_profile.user
                if change
                in (
                    ReportHistory.ChangeChoices.CREATED,
                    ReportHistory.ChangeChoices.UPDATED,
                )
                else self.education_officer
            )
            ReportHistory.objects.create(
                report=report,
                user=reviewer,
                role=reviewer.role,
                change=change,
                description=(
                    "Rejected for testing."
                    if change == ReportHistory.ChangeChoices.REJECTED
                    else None
                ),
            )
        return report

    def calculate(
        self,
        *,
        year: int | None = None,
        month: int | None = None,
        user: User | None = None,
    ) -> None:
        WageService(
            year=year or self.calculation_year,
            month=month or self.calculation_month,
            user=user or self.finance_officer,
        ).calculate_wages()

    def get_wage(
        self,
        *,
        teacher_profile: TeacherProfile | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> Wage:
        return Wage.objects.get(
            teacher_profile=teacher_profile or self.teacher_profile,
            year=year or self.calculation_year,
            month=month or self.calculation_month,
        )

    def test_only_sessions_in_requested_month_are_counted_including_december_branch(
        self,
    ) -> None:
        semester = self.create_semester(
            name="Winter 2026",
            start_date=date(2026, 12, 1),
            end_date=date(2027, 1, 31),
        )
        self.create_rate(semester=semester)
        course = self.create_course(name="Winter Course", semester=semester)
        december_session = self.create_session(
            course=course,
            session_date=date(2026, 12, 31),
        )
        january_session = self.create_session(
            course=course,
            session_date=date(2027, 1, 1),
        )
        self.create_report(session=december_session)
        self.create_report(session=january_session)

        self.calculate(year=2026, month=12)

        self.assertEqual(
            self.get_wage(year=2026, month=12).amount,
            Decimal("200000.00"),
        )

    def test_summer_coefficient_is_applied(self) -> None:
        summer = self.create_semester(
            name="Summer 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            is_summer=True,
        )
        self.create_rate(semester=summer)
        course = self.create_course(name="Summer Course", semester=summer)
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=session)

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("220000.00"))

    def test_delay_penalty_is_one_percent_per_hour(self) -> None:
        self.create_rate()
        course = self.create_course()
        fifty_hour_delay = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        ninety_nine_hour_delay = self.create_session(
            course=course,
            session_date=date(2026, 1, 11),
        )
        self.create_report(session=fifty_hour_delay, delay_time=50)
        self.create_report(session=ninety_nine_hour_delay, delay_time=99)

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("102000.00"))

    def test_report_delayed_by_100_hours_or_more_contributes_zero(self) -> None:
        self.create_rate()
        course = self.create_course()
        for day, delay_time in ((10, 100), (11, 101)):
            session = self.create_session(
                course=course,
                session_date=date(2026, 1, day),
            )
            self.create_report(session=session, delay_time=delay_time)

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("0.00"))

    def test_missing_wage_rate_aborts_calculation_without_creating_wages(self) -> None:
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=session)

        with self.assertRaisesMessage(
            ValidationError,
            "There are teachers without wage rate!",
        ):
            self.calculate()

        self.assertFalse(Wage.objects.exists())

    def test_soft_deleted_wage_rate_is_treated_as_missing(self) -> None:
        wage_rate = self.create_rate()
        wage_rate.soft_delete(updated_by=self.finance_officer)
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=session)

        with self.assertRaisesMessage(
            ValidationError,
            "There are teachers without wage rate!",
        ):
            self.calculate()

    def test_pending_created_report_aborts_calculation(self) -> None:
        self.create_rate()
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(
            session=session,
            changes=(ReportHistory.ChangeChoices.CREATED,),
        )

        with self.assertRaisesMessage(
            ValidationError,
            "There are reports which are not reviewed!",
        ):
            self.calculate()

        self.assertFalse(Wage.objects.exists())

    def test_latest_report_history_controls_review_status(self) -> None:
        self.create_rate()
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(
            session=session,
            changes=(
                ReportHistory.ChangeChoices.CREATED,
                ReportHistory.ChangeChoices.REJECTED,
                ReportHistory.ChangeChoices.UPDATED,
            ),
        )

        with self.assertRaisesMessage(
            ValidationError,
            "There are reports which are not reviewed!",
        ):
            self.calculate()

    def test_missing_report_during_active_assignment_zeroes_teacher_wage(self) -> None:
        self.create_rate()
        course = self.create_course()
        approved_session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=approved_session)
        self.create_session(
            course=course,
            session_date=date(2026, 1, 11),
        )

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("0.00"))

    def test_missing_report_outside_assignment_does_not_zero_teacher_wage(
        self,
    ) -> None:
        self.create_rate()
        course = self.create_course(
            started_at=date(2026, 1, 2),
            ended_at=date(2026, 1, 31),
        )
        self.create_session(
            course=course,
            session_date=date(2026, 1, 1),
        )
        approved_session = self.create_session(
            course=course,
            session_date=date(2026, 1, 2),
        )
        self.create_report(session=approved_session)

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("200000.00"))

    def test_calculation_creates_zero_wage_for_teacher_without_sessions(self) -> None:
        inactive_user = User.objects.create_user(
            "inactive-teacher@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        inactive_profile = self.create_teacher_profile(
            inactive_user,
            first_name="Inactive",
            last_name="Teacher",
        )
        self.create_rate()
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=session)

        self.calculate()

        self.assertEqual(self.get_wage().amount, Decimal("200000.00"))
        self.assertEqual(
            self.get_wage(teacher_profile=inactive_profile).amount,
            Decimal("0.00"),
        )

    def test_recalculation_upserts_wage_and_preserves_original_creator(self) -> None:
        wage_rate = self.create_rate()
        course = self.create_course()
        session = self.create_session(
            course=course,
            session_date=date(2026, 1, 10),
        )
        self.create_report(session=session)
        self.calculate()
        original_wage = self.get_wage()

        second_finance_officer = User.objects.create_user(
            "second-fio@example.com",
            "finance-password",
            role=User.RoleChoices.FINANCE_OFFICER,
        )
        wage_rate.amount = Decimal("300000.00")
        wage_rate.updated_by = second_finance_officer
        wage_rate.save(update_fields=("amount", "updated_by", "updated_at"))

        self.calculate(user=second_finance_officer)

        recalculated_wage = self.get_wage()
        self.assertEqual(Wage.objects.count(), 1)
        self.assertEqual(recalculated_wage.pk, original_wage.pk)
        self.assertEqual(recalculated_wage.amount, Decimal("300000.00"))
        self.assertEqual(recalculated_wage.created_by, self.finance_officer)
        self.assertEqual(recalculated_wage.updated_by, second_finance_officer)
