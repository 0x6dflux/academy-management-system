from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from account.models import TeacherProfile, User
from account.serializers import (
    TeacherProfileEducationOfficerRoleSerializer,
    TeacherProfileTeacherRoleSerializer,
)
from account.views import TeacherProfileAPIView, UserCreateAPIView, UserRetrieveAPIView

USER = User


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
        self.teacher1 = USER.objects.create_user(
            "TCH1@example.com",
            "3-tch",
            role="TCH",
        )
        self.teacher2 = USER.objects.create_user(
            "TCH2@example.com",
            "4_tch",
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
        kwargs = {"-e": "test_username@example.com", "-p": "te$T/12356", "-r": "TCH"}
        call_command(
            "create_user",
            "-e",
            kwargs["-e"],
            "-p",
            kwargs["-p"],
            "-r",
            kwargs["-r"],
            stdout=out,
        )

        created_user = USER.objects.get(email=kwargs["-e"])
        self.assertIn(
            f"'{kwargs['-e']}' with 'id={created_user.pk}' created successfully.",
            out.getvalue(),
        )
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
            "Email is not available!",
            call_command,
            "create_user",
            "-e",
            "ADM@example.com",
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
            "-e",
            "ADM@example.com",
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
                401,
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
            "email": "test-finance-officer@example.com",
            "password": "te$t1",
            "role": "FIO",
        }
        EDO_body = {
            "email": "test-education-officer@example.com",
            "password": "te$t2",
            "role": "EDO",
        }
        TCH_body = {
            "email": "test-teacher@example.com",
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
            f"{FIO_body['email']} has not been created!",
        )
        self.assertEqual(
            EDO_response.status_code,
            201,
            f"{EDO_body['email']} has not been created!",
        )
        self.assertEqual(
            TCH_response.status_code,
            201,
            f"{TCH_body['email']} has not been created!",
        )
        self.assertEqual(
            FIO_response.data["email"],
            FIO_body["email"],
            "Invalid FIO email!",
        )
        self.assertEqual(
            FIO_response.data["role"],
            FIO_body["role"],
            "Invalid FIO role!",
        )
        self.assertEqual(
            EDO_response.data["email"],
            EDO_body["email"],
            "Invalid EDO email!",
        )
        self.assertEqual(
            EDO_response.data["role"],
            EDO_body["role"],
            "Invalid EDO role!",
        )
        self.assertEqual(
            TCH_response.data["email"],
            TCH_body["email"],
            "Invalid TCH email!",
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
                response.data["email"],
                user.email,
                "Invalid email!",
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
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
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
        response.data.pop("status")

        self.assertEqual(
            response.status_code,
            201,
            "The response of creating a new profile is not 201!",
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
                "email": self.teacher1.email,
                "role": self.teacher1.role,
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
        response.data.pop("status")

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
            response.data.pop("status")

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

    def test_retrieve_teacher_profile(self):
        # creating a teacher profile
        method = "post"
        url = reverse("account:teacher-profile")
        create_teacher_profile_body = {
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
        response.data.pop("status")

        # calling endpoint with a TCH role
        method = "get"
        url = reverse("account:teacher-profile")
        body = {}
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
        response.data.pop("status")

        self.assertEqual(response.status_code, 200, "Unsuccessful retrieve method!")
        user = response.data.pop("user")
        self.assertEqual(
            user,
            {
                "email": self.teacher1.email,
                "role": self.teacher1.role,
            },
            "Inconsistent user info!",
        )
        self.assertEqual(
            response.data,
            create_teacher_profile_body,
            "Inconsistent teacher1 profile info!",
        )

        # calling endpoint with an EDO role
        method = "get"
        url = reverse("account:teacher-profile")
        body = {}
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.education_officer,
        )
        response.data.pop("status")
        profiles = response.data.pop("profiles")

        deserialized = TeacherProfileEducationOfficerRoleSerializer(
            TeacherProfile.all_objects.first()
        )

        self.assertEqual(response.status_code, 200, "Unsuccessful list method!")
        self.assertEqual(
            profiles,
            [deserialized.data],
            "Inconsistent profiles info!",
        )

    def test_put_teacher_profile(self):
        # creating a teacher profile
        method = "post"
        url = reverse("account:teacher-profile")
        create_teacher_profile_body = {
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
        response.data.pop("status")

        # calling endpoint with a TCH role
        method = "put"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "MAHDI",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234560",
            "landline_number": "0982112345670",
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
        response.data.pop("status")
        response.data.pop("user")

        self.assertEqual(response.status_code, 200, "Unsuccessful put method!")
        self.assertEqual(
            response.data,
            body,
            "Inconsistent profile info!",
        )

    def test_patch_teacher_profile(self):
        # creating a teacher profile
        method = "post"
        url = reverse("account:teacher-profile")
        create_teacher_profile_body = {
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
        response.data.pop("status")

        # calling endpoint with a TCH role
        method = "patch"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "MAHDI",
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
        response.data.pop("status")

        deserialized = TeacherProfileTeacherRoleSerializer(
            TeacherProfile.all_objects.first()
        )

        self.assertEqual(response.status_code, 200, "Unsuccessful patch method!")
        self.assertEqual(
            response.data,
            deserialized.data,
            "Inconsistent profile info!",
        )

    def test_delete_teacher_profile(self):
        # creating a teacher profile
        method = "post"
        url = reverse("account:teacher-profile")
        create_teacher_profile_body = {
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.simulate_server(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
        profile_id = TeacherProfile.all_objects.get(user=self.teacher1).pk

        # calling endpoint with an EDO role
        request = self.factory.delete(
            f"{reverse('account:teacher-profile')}?id={profile_id}"
        )
        view = TeacherProfileAPIView.as_view()
        force_authenticate(request, self.education_officer)

        response = view(request)

        self.assertEqual(response.status_code, 204, "Unsuccessful delete method!")
        self.assertTrue(
            TeacherProfile.all_objects.get(pk=profile_id).is_deleted,
            "Profile was not soft deleted!",
        )
