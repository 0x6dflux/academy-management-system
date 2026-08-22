from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from account.models import TeacherProfile, User
from education.models import School, Semester
from finance.models import Wage, WageRate
from finance.views import HomeAPIView

USER = User


class EducationTestCase(TestCase):
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

    def test_education_home_permissions(self):
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
