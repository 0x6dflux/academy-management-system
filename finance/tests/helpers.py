from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from account.models import TeacherProfile, User
from education.models import School, Semester
from finance.models import Wage, WageRate


class FinanceTestCase(TestCase):
    """Shared, valid finance-domain fixtures for focused test cases."""

    admin: User
    finance_officer: User
    education_officer: User
    teacher: User
    other_teacher: User
    teacher_profile: TeacherProfile
    other_teacher_profile: TeacherProfile
    school: School
    semester: Semester
    client: APIClient

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            "finance-admin@example.com",
            "admin-password",
            role=User.RoleChoices.ADMIN,
        )
        cls.finance_officer = User.objects.create_user(
            "finance-officer@example.com",
            "finance-password",
            role=User.RoleChoices.FINANCE_OFFICER,
        )
        cls.education_officer = User.objects.create_user(
            "finance-education@example.com",
            "education-password",
            role=User.RoleChoices.EDUCATION_OFFICER,
        )
        cls.teacher = User.objects.create_user(
            "finance-teacher@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        cls.other_teacher = User.objects.create_user(
            "finance-other-teacher@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        cls.teacher_profile = TeacherProfile.objects.create(
            user=cls.teacher,
            first_name="First",
            last_name="Teacher",
            mobile_number="09120000001",
            landline_number="02130000001",
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.other_teacher_profile = TeacherProfile.objects.create(
            user=cls.other_teacher,
            first_name="Second",
            last_name="Teacher",
            mobile_number="09120000002",
            landline_number="02130000002",
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.school = School.objects.create(
            name="Finance Test School",
            email="finance-school@example.com",
            landline_number="02130000003",
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.semester = Semester.objects.create(
            school=cls.school,
            name="Finance Test Semester",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            is_summer_semester=False,
            created_by=cls.admin,
            updated_by=cls.admin,
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def create_wage(
        self,
        *,
        teacher_profile: TeacherProfile | None = None,
        year: int = 2025,
        month: int = Wage.MonthChoices.MONTH_01,
        amount: Decimal = Decimal("1000.00"),
        created_by: User | None = None,
        updated_by: User | None = None,
    ) -> Wage:
        modifier = created_by or self.admin
        return Wage.objects.create(
            teacher_profile=teacher_profile or self.teacher_profile,
            year=year,
            month=month,
            amount=amount,
            created_by=modifier,
            updated_by=updated_by or modifier,
        )

    def create_wage_rate(
        self,
        *,
        semester: Semester | None = None,
        teacher_profile: TeacherProfile | None = None,
        amount: Decimal = Decimal("200000.00"),
        created_by: User | None = None,
        updated_by: User | None = None,
    ) -> WageRate:
        modifier = created_by or self.admin
        return WageRate.objects.create(
            semester=semester or self.semester,
            teacher_profile=teacher_profile or self.teacher_profile,
            amount=amount,
            created_by=modifier,
            updated_by=updated_by or modifier,
        )
