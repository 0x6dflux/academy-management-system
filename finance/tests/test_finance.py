from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

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
from finance.views import HomeAPIView
from services.wage_service import WageService

USER = User


class FinanceTestCase(TestCase):
    def simulate_server(
        self,
        method: str,
        url: str,
        body: dict,
        view_class: type[APIView],
        *,
        authentication=False,
        user: User | None = None,
    ) -> Response:
        request = getattr(self.factory, method)(url, body)
        view = view_class.as_view()
        if authentication:
            force_authenticate(request, user)

        return view(request)

    def setUp(self) -> None:
        # ==================
        # setup the database
        # ==================
        # Admin
        self.admin = USER.objects.create_user(
            "ADM@example.com",
            "0@dmin",
            role="ADM",
        )
        # Finance_Officer
        self.finance_officer = USER.objects.create_user(
            "FIO@example.com",
            "1/fio",
            role="FIO",
        )
        # Education_Officer
        self.education_officer = USER.objects.create_user(
            "EDO@example.com",
            "2#edo",
            role="EDO",
        )
        # Teacher
        self.teacher = USER.objects.create_user(
            "TCH@example.com",
            "3-tch",
            role="TCH",
        )

        # =================
        # setup the request
        # =================
        self.http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
        self.factory = APIRequestFactory()

    def test_finance_home_rejects_unsupported_methods(self):
        url = reverse("finance:home")
        view_class = HomeAPIView

        for method in self.http_methods - {"get"}:
            response = self.simulate_server(
                method,
                url,
                {},
                view_class,
                authentication=True,
                user=self.admin,
            )
            self.assertEqual(
                response.status_code,
                405,
                f"{self.admin} got access with {method}",
            )

    def test_finance_home_permissions(self):
        method = "get"
        url = reverse("finance:home")
        view_class = HomeAPIView

        # anonymous user
        response = self.simulate_server(
            method,
            url,
            {},
            view_class,
        )
        self.assertEqual(
            response.status_code,
            401,
            f"Anonymous user got access with {method}!",
        )

        # authenticated user
        response = self.simulate_server(
            method,
            url,
            {},
            view_class,
            authentication=True,
            user=self.education_officer,
        )
        self.assertEqual(
            response.status_code,
            403,
            f"{self.education_officer} got access with {method}",
        )

        response = self.simulate_server(
            method,
            url,
            {},
            view_class,
            authentication=True,
            user=self.teacher,
        )
        self.assertEqual(
            response.status_code,
            403,
            f"{self.teacher} got access with {method}",
        )

        response = self.simulate_server(
            method,
            url,
            {},
            view_class,
            authentication=True,
            user=self.finance_officer,
        )
        self.assertEqual(
            response.status_code,
            200,
            f"{self.finance_officer} did not get access with {method}",
        )

        response = self.simulate_server(
            method,
            url,
            {},
            view_class,
            authentication=True,
            user=self.admin,
        )
        self.assertEqual(
            response.status_code,
            200,
            f"{self.admin} did not get access with {method}",
        )


class FinanceModelsTestCase(TestCase):
    def setUp(self) -> None:
        self.admin = USER.objects.create_user(
            "ADM@example.com",
            "0@dmin",
            role="ADM",
        )
        teacher = USER.objects.create_user(
            "TCH@example.com",
            "3-tch",
            role="TCH",
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=teacher,
            first_name="Mahdi",
            last_name="Ahmadi",
            mobile_number="091234567890",
            landline_number="02112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.school = School.objects.create(
            name="Finance School",
            email="finance@example.com",
            landline_number="02111111111",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.semester = Semester.objects.create(
            school=self.school,
            name="Spring",
            start_date=now().date() - timedelta(days=30),
            end_date=now().date() + timedelta(days=30),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

    def test_wage_str_representation(self) -> None:
        wage = Wage.objects.create(
            teacher_profile=self.teacher_profile,
            year=now().year,
            month=Wage.MonthChoices.MONTH_01,
            amount=Decimal("12500.00"),
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.assertEqual(
            str(wage),
            f"{wage.year}-{wage.month.label}",
        )

    def test_wage_rate_str_representation(self) -> None:
        wage_rate = WageRate.objects.create(
            semester=self.semester,
            teacher_profile=self.teacher_profile,
            amount=Decimal("25000.00"),
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.assertEqual(
            str(wage_rate),
            f"{self.teacher_profile}-{self.semester}",
        )


class WageServiceCalculationTestCase(TestCase):
    calculation_year = 2026
    calculation_month = 1
    base_wage_rate = Decimal("200000.00")

    def setUp(self) -> None:
        self.admin = USER.objects.create_user(
            "wage-admin@example.com",
            "admin-password",
            role=USER.RoleChoices.ADMIN,
        )
        self.finance_officer = USER.objects.create_user(
            "wage-fio@example.com",
            "fio-password",
            role=USER.RoleChoices.FINANCE_OFFICER,
        )
        self.education_officer = USER.objects.create_user(
            "wage-edo@example.com",
            "edo-password",
            role=USER.RoleChoices.EDUCATION_OFFICER,
        )
        self.teacher = USER.objects.create_user(
            "wage-teacher@example.com",
            "teacher-password",
            role=USER.RoleChoices.TEACHER,
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Wage",
            last_name="Teacher",
            mobile_number="09120000000",
            landline_number="02130000000",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.school = School.objects.create(
            name="Wage Test School",
            email="wage-test@example.com",
            landline_number="02130000001",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.semester = Semester.objects.create(
            school=self.school,
            name="January 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )
        WageRate.objects.create(
            semester=self.semester,
            teacher_profile=self.teacher_profile,
            amount=self.base_wage_rate,
            created_by=self.finance_officer,
            updated_by=self.finance_officer,
        )

    def create_course(self, session_length: int, name: str) -> Course:
        course = Course.objects.create(
            semester=self.semester,
            name=name,
            level=Course.LevelChoices.BASIC,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            sessions_length=session_length,
            created_by=self.admin,
            updated_by=self.admin,
        )
        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=course,
            started_at=course.start_date,
            ended_at=course.end_date,
            created_by=self.admin,
            updated_by=self.admin,
        )
        return course

    def create_reviewed_report(
        self,
        *,
        course: Course,
        day: int,
        delay_time: int = 0,
        final_change: int = ReportHistory.ChangeChoices.APPROVED,
    ) -> Report:
        session_end_times: dict[int, time] = {
            Course.SessionLengthChoices.MIN60: time(10, 0),
            Course.SessionLengthChoices.MIN90: time(10, 30),
            Course.SessionLengthChoices.MIN120: time(11, 0),
        }
        session = Session.objects.create(
            course=course,
            date=date(self.calculation_year, self.calculation_month, day),
            start_time=time(9, 0),
            end_time=session_end_times[course.sessions_length],
            created_by=self.admin,
            updated_by=self.admin,
        )
        report = Report.objects.create(
            session=session,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Wage calculation test report",
            number_of_attendees=10,
            number_of_absentees=0,
            is_delayed=delay_time > 0,
            delay_time=delay_time,
            created_by=self.teacher,
            updated_by=self.teacher,
        )
        ReportHistory.objects.create(
            report=report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )
        ReportHistory.objects.create(
            report=report,
            user=self.education_officer,
            role=USER.RoleChoices.EDUCATION_OFFICER,
            change=final_change,
            description=(
                "The report was rejected."
                if final_change == ReportHistory.ChangeChoices.REJECTED
                else None
            ),
        )
        return report

    def calculate_wages(self) -> None:
        WageService(
            year=self.calculation_year,
            month=self.calculation_month,
            user=self.finance_officer,
        ).calculate_wages()

    def test_example_wage_calculation(
        self,
    ) -> None:
        course_90 = self.create_course(
            Course.SessionLengthChoices.MIN90,
            "90-minute course",
        )
        course_60 = self.create_course(
            Course.SessionLengthChoices.MIN60,
            "60-minute course",
        )
        course_120 = self.create_course(
            Course.SessionLengthChoices.MIN120,
            "120-minute course",
        )

        for day in range(1, 11):
            self.create_reviewed_report(course=course_90, day=day)
        for day in range(11, 13):
            self.create_reviewed_report(course=course_60, day=day)
        self.create_reviewed_report(course=course_120, day=13)

        # delay_time measures hours after the 48-hour submission deadline.
        # This 90-minute session therefore contributes 200,000 * 0 = 0.
        self.create_reviewed_report(course=course_90, day=14, delay_time=100)

        self.calculate_wages()

        wage = Wage.objects.get(
            teacher_profile=self.teacher_profile,
            year=self.calculation_year,
            month=self.calculation_month,
        )
        self.assertEqual(wage.amount, Decimal("2_540_000.00"))

    def test_calculate_wages_creates_zero_wage_for_teacher_without_approved_report(
        self,
    ) -> None:
        course = self.create_course(
            Course.SessionLengthChoices.MIN90,
            "Rejected-report course",
        )
        self.create_reviewed_report(
            course=course,
            day=1,
            final_change=ReportHistory.ChangeChoices.REJECTED,
        )

        self.calculate_wages()

        wages = Wage.objects.filter(
            teacher_profile=self.teacher_profile,
            year=self.calculation_year,
            month=self.calculation_month,
        )
        self.assertTrue(wages.exists())
        self.assertEqual(wages.get().amount, Decimal("0.00"))

    def test_calculate_wages_includes_report_submitted_at_exact_48_hour_boundary(
        self,
    ) -> None:
        course = self.create_course(
            Course.SessionLengthChoices.MIN90,
            "48-hour-boundary course",
        )

        # The report serializer represents exactly 48 hours after the session
        # as not delayed, with zero hours beyond the submission deadline.
        self.create_reviewed_report(course=course, day=1, delay_time=0)

        self.calculate_wages()

        wage = Wage.objects.get(
            teacher_profile=self.teacher_profile,
            year=self.calculation_year,
            month=self.calculation_month,
        )
        self.assertEqual(wage.amount, self.base_wage_rate)
