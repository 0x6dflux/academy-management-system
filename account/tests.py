from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from account.models import TeacherProfile
from account.views import TeacherProfileAPIView, UserCreateAPIView, UserRetrieveAPIView

if TYPE_CHECKING:
    from account.models import User


USER: User = get_user_model()  # type: ignore


class AccountTestCase(TestCase):
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
            username="admin_ADM",
            password="0@dmin",
            role="ADM",
        )
        # Finance_Officer
        self.finance_officer = USER.objects.create_user(
            username="mhm_FIO",
            password="1/fio",
            role="FIO",
        )
        # Education_Officer
        self.education_officer = USER.objects.create_user(
            username="ftm_EDO",
            password="2#edo",
            role="EDO",
        )
        # Teacher
        self.teacher1 = USER.objects.create_user(
            username="mhd_TCH",
            password="3-tch",
            role="TCH",
        )
        self.teacher2 = USER.objects.create_user(
            username="msd_TCH",
            password="4_tch",
            role="TCH",
        )

        # =================
        # setup the request
        # =================
        self.http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
        self.factory = APIRequestFactory()

    def test_create_user_with_management_command(self) -> None:
        number_of_users_before_call_command = USER.objects.count()

        out = StringIO()
        kwargs = {"-u": "test_username", "-p": "te$T/12356", "-r": "TCH"}
        call_command(
            "create_user",
            "-u",
            kwargs["-u"],
            "-p",
            kwargs["-p"],
            "-r",
            kwargs["-r"],
            stdout=out,
        )

        created_user = USER.objects.get(username=kwargs["-u"])
        self.assertIn(
            f"'{kwargs['-u']}' with 'id={created_user.pk}' created successfully.",
            out.getvalue(),
        )
        # self.assertEqual(created_user.username, kwargs["-u"], "invalid username")
        self.assertTrue(created_user.check_password(kwargs["-p"]), "invalid password")
        self.assertEqual(created_user.role, kwargs["-r"], "invalid role")
        self.assertEqual(
            USER.objects.count(),
            number_of_users_before_call_command + 1,
            "Inconsistent number of users",
        )

    def test_not_available_username_exception_with_management_command(self) -> None:
        number_of_users_before_call_command = USER.objects.count()

        self.assertRaisesMessage(
            CommandError,
            "Username is not available!",
            call_command,
            "create_user",
            "-u",
            "admin_ADM",
            "-p",
            "0@dmin",
            "-r",
            "ADM",
        )

        self.assertEqual(
            USER.objects.count(),
            number_of_users_before_call_command,
            "Inconsistent number of users",
        )

    def test_no_admin_found_exception_with_management_command(self) -> None:
        # removing the user with ADMIN role
        USER.objects.get(role=USER.RoleChoices.ADMIN).delete()

        number_of_users_before_call_command = USER.objects.count()

        self.assertRaisesMessage(
            CommandError,
            "No user with admin role found!",
            call_command,
            "create_user",
            "-u",
            "admin_ADM",
            "-p",
            "0@dmin",
            "-r",
            "ADM",
        )

        self.assertEqual(
            USER.objects.count(),
            number_of_users_before_call_command,
            "Inconsistent number of users",
        )

        # recreate the user with ADMIN role
        # to not interrupt the other tests
        # USER.objects.create_user(username="admin_ADM", password="0@dmin", role="ADM")
        # each test is performed in a transaction
        # and the `setUp()` is run before each test
        # so, recreating the user with ADMIN role is not necessary

    def test_create_user_rejects_unsupported_methods(self):
        url = reverse("account:create-user")
        view_class = UserCreateAPIView

        for method in self.http_methods - {"post"}:
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

    def test_create_user_rejects_user_without_admin_role(self):
        url = reverse("account:create-user")
        view_class = UserCreateAPIView

        for method in self.http_methods:
            # anonymous user
            response = self.simulate_server(
                method,
                url,
                {},
                view_class,
            )
            self.assertEqual(
                response.status_code,
                403,
                f"{method} allows unauthenticated user!",
            )

            # all users except admin
            for user in USER.objects.exclude(role=USER.RoleChoices.ADMIN):
                response = self.simulate_server(
                    method,
                    url,
                    {},
                    view_class,
                    authentication=True,
                    user=user,
                )
                self.assertEqual(
                    response.status_code,
                    403,
                    f"{user} got access with {method}",
                )

    def test_create_user_admin_creates_a_new_user(self):
        number_of_users_before_call_command = USER.objects.count()

        url = reverse("account:create-user")
        view_class = UserCreateAPIView

        FIO_body = {
            "username": "test-finance-officer",
            "password": "te$t1",
            "role": "FIO",
        }
        EDO_body = {
            "username": "test-education-officer",
            "password": "te$t2",
            "role": "EDO",
        }
        TCH_body = {
            "username": "test-teacher",
            "password": "te$t3",
            "role": "TCH",
        }

        # creating FIO
        FIO_response = self.simulate_server(
            "post",
            url,
            FIO_body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        # creating EDO
        EDO_response = self.simulate_server(
            "post",
            url,
            EDO_body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        # creating TCH
        TCH_response = self.simulate_server(
            "post",
            url,
            TCH_body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        self.assertEqual(
            USER.objects.count(),
            number_of_users_before_call_command + 3,
            "A test-user might not be created!",
        )
        self.assertEqual(
            FIO_response.status_code,
            201,
            f"{FIO_body['username']} has not been created!",
        )
        self.assertEqual(
            EDO_response.status_code,
            201,
            f"{EDO_body['username']} has not been created!",
        )
        self.assertEqual(
            TCH_response.status_code,
            201,
            f"{TCH_body['username']} has not been created!",
        )
        self.assertEqual(
            FIO_response.data["username"],
            FIO_body["username"],
            "Invalid FIO username!",
        )
        self.assertEqual(
            FIO_response.data["role"],
            FIO_body["role"],
            "Invalid FIO role!",
        )
        self.assertEqual(
            EDO_response.data["username"],
            EDO_body["username"],
            "Invalid EDO username!",
        )
        self.assertEqual(
            EDO_response.data["role"],
            EDO_body["role"],
            "Invalid EDO role!",
        )
        self.assertEqual(
            TCH_response.data["username"],
            TCH_body["username"],
            "Invalid TCH username!",
        )
        self.assertEqual(
            TCH_response.data["role"],
            TCH_body["role"],
            "Invalid TCH role!",
        )

    def test_account_me_rejects_unsupported_methods(self):
        url = reverse("account:me")
        view_class = UserRetrieveAPIView

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

    def test_login_with_account_me(self):
        url = reverse("account:me")
        view_class = UserRetrieveAPIView

        for user in USER.objects.all():
            response = self.simulate_server(
                "get",
                url,
                {},
                view_class,
                authentication=True,
                user=user,
            )
            self.assertEqual(response.status_code, 200, "Unsuccessful")
            self.assertEqual(
                response.data["username"],
                user.username,
                "Invalid username!",
            )
            self.assertEqual(
                response.data["role"],
                user.role,
                "Invalid role!",
            )

    def test_teacher_profile_rejects_unsupported_methods(self):
        url = reverse("account:teacher-profile")
        view_class = TeacherProfileAPIView

        for method in {"head", "options"}:
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

    def test_teacher_profile_permissions(self):
        url = reverse("account:teacher-profile")
        view_class = TeacherProfileAPIView

        for method in self.http_methods - {"head", "options"}:
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
                f"Anonymous user got access with {method}",
            )

            # authenticated user
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
                403,
                f"{self.finance_officer} got access with {method}",
            )

    def test_create_teacher_profile(self):
        # number of teacher profiles before creating a new profile
        number_of_profiles = TeacherProfile.all_objects.count()

        # successful scenario
        method = "post"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "phone_number": "09123456789",
            "emergency_phone_number": "02112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

        self.assertEqual(
            response.status_code,
            201,
            "The response of creating a new profile is not 200!",
        )

        self.assertEqual(
            number_of_profiles + 1,
            TeacherProfile.all_objects.count(),
            "Inconsistent number of profiles!",
        )

        user = response.data.pop("user")
        self.assertEqual(
            user,
            {
                "username": self.teacher1.username,
                "role": self.teacher1.role,
                "email": self.teacher1.email,
            },
            "Inconsistent user info!",
        )
        self.assertEqual(response.data, body, "Inconsistent profile info!")

        # updating the number of profiles
        number_of_profiles = TeacherProfile.all_objects.count()

        # teacher profile exists
        response = self.simulate_server(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

        self.assertEqual(
            response.status_code,
            400,
            "The response of creating a new profile is not 400!",
        )

        self.assertEqual(
            number_of_profiles,
            TeacherProfile.all_objects.count(),
            "Inconsistent number of profiles!",
        )

        self.assertEqual(
            response.data,
            {"message": "The profile already exists!"},
            "Inconsistent response message!",
        )

        # updating the number of profiles
        number_of_profiles = TeacherProfile.all_objects.count()

        # missing or bad data in request body
        bodies = [
            {
                "first_name": "Mahdi",
                "last_name": "Mohammadi",
                "phone_number": "09123456789",
            },
            {
                "firstname": "Mahdi",
                "last_name": "Mohammadi",
                "phone_number": "09123456789",
                "emergency_phone_number": "02112345678",
            },
        ]

        for body in bodies:
            response = self.simulate_server(
                method,
                url,
                body,
                view_class,
                authentication=True,
                user=self.teacher1,
            )

            self.assertEqual(
                response.status_code,
                400,
                "The response of creating a new profile is not 400!",
            )

            self.assertEqual(
                number_of_profiles,
                TeacherProfile.all_objects.count(),
                "Inconsistent number of profiles!",
            )

            self.assertEqual(
                response.data,
                {"message": "The profile already exists!"},
                "Inconsistent response message!",
            )
