from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from account.models import TeacherProfile, User
from account.serializers import (
    TeacherProfileEducationOfficerRoleSerializer,
    TeacherProfileTeacherRoleSerializer,
)
from account.views import TeacherProfileAPIView, UserCreateAPIView, UserRetrieveAPIView
from system.utils import EndpointTestsMixin, ModelTestsMixin

USER = User


class AccountModelsTestCases(TestCase, ModelTestsMixin):
    def setUp(self) -> None:
        self.admin = USER.objects.create_user(
            "admin-test@example.com",
            "123",
            role="ADM",
        )

        self.teacher = USER.objects.create_user("mhd@google.com", "123", role="TCH")

    def test_user(self) -> None:
        user_instance = USER.objects.get(id=self.teacher.id)

        self.assertEqual(user_instance.email, self.teacher.email, "Inconsistent email!")
        self.assertEqual(user_instance.role, self.teacher.role, "Inconsistent role!")
        self.assertEqual(
            user_instance.password,
            self.teacher.password,
            "Inconsistent password!",
        )

    def test_teacher_profile(self) -> None:
        profile_data = {
            "user_id": self.teacher.id,
            "first_name": "Mahdi",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }

        self.run_model_equal_assertions(
            TeacherProfile,
            profile_data,
            f"{profile_data['first_name']} {profile_data['last_name']}",
        )


class AccountEndpointsTestCases(TestCase, EndpointTestsMixin):
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
            response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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
                response = self.run_server_with_APIRequestFactory(
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
        FIO_response = self.run_server_with_APIRequestFactory(
            "post",
            url,
            FIO_body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        # creating EDO
        EDO_response = self.run_server_with_APIRequestFactory(
            "post",
            url,
            EDO_body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        # creating TCH
        TCH_response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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

        for method in ("head", "options"):
            response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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

        response = self.run_server_with_APIRequestFactory(
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
        response = self.run_server_with_APIRequestFactory(
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
            response = self.run_server_with_APIRequestFactory(
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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

        # calling endpoint with a TCH role
        method = "get"
        url = reverse("account:teacher-profile")
        body = {}
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.education_officer,
        )

        deserialized = TeacherProfileEducationOfficerRoleSerializer(
            TeacherProfile.all_objects.first()
        )

        self.assertEqual(response.status_code, 200, "Unsuccessful list method!")
        self.assertEqual(
            response.data,
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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )
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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            create_teacher_profile_body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

        # calling endpoint with a TCH role
        method = "patch"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "MAHDI",
        }
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

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

        response = self.run_server_with_APIRequestFactory(
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


class AccountTeacherProfileEdgeCasesTestCase(TestCase, EndpointTestsMixin):
    def setUp(self):
        self.admin = USER.objects.create_user("ADM@example.com", "0@dmin", role="ADM")
        self.education_officer = USER.objects.create_user(
            "EDO@example.com", "2#edo", role="EDO"
        )
        self.teacher_no_profile = USER.objects.create_user(
            "no-profile@example.com", "123", role="TCH"
        )
        self.teacher1 = USER.objects.create_user(
            "TCH1@example.com", "3-tch", role="TCH"
        )
        self.factory = APIRequestFactory()

    def test_teacher_get_no_profile(self):
        url = reverse("account:teacher-profile")
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            "get",
            url,
            {},
            view_class,
            authentication=True,
            user=self.teacher_no_profile,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Create your profile."})

    def test_delete_without_id_query_param(self):
        url = reverse("account:teacher-profile")
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            "delete",
            url,
            {},
            view_class,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.data)
        self.assertIn("example", response.data)

    def test_delete_nonexistent_profile_id(self):
        request = self.factory.delete(f"{reverse('account:teacher-profile')}?id=99999")
        view = TeacherProfileAPIView.as_view()
        force_authenticate(request, self.education_officer)

        self.assertRaises(
            TeacherProfile.DoesNotExist,
            lambda: view(request),
        )

    def test_admin_can_create_teacher_profile(self):
        method = "post"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "Admin",
            "last_name": "User",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.admin,
        )

        self.assertEqual(response.status_code, 201)

    def test_teacher_profile_create_validates_name_with_digits(self):
        method = "post"
        url = reverse("account:teacher-profile")
        body = {
            "first_name": "Mahdi123",
            "last_name": "Mohammadi",
            "mobile_number": "0989361234567",
            "landline_number": "0982112345678",
        }
        view_class = TeacherProfileAPIView

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.teacher1,
        )

        self.assertEqual(response.status_code, 400)


class AccountUserManagerTestCase(TestCase):
    def test_create_superuser_flags(self):
        superuser = USER.objects.create_superuser(
            "super@example.com", "superpass", role="ADM"
        )
        self.assertTrue(superuser.is_staff, "Superuser should have is_staff=True")
        self.assertTrue(
            superuser.is_superuser, "Superuser should have is_superuser=True"
        )

    def test_create_user_with_valid_data(self):
        user = USER.objects.create_user("new@example.com", "password123", role="TCH")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.role, "TCH")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.is_staff)

    def test_create_superuser_with_none_email(self):
        self.assertRaises(
            ValueError,
            USER.objects.create_superuser,
            None,
            "password",
            role="ADM",
        )

    def test_manager_objects_excludes_deleted(self):
        user = USER.objects.create_user("deleted@example.com", "123", role="TCH")
        count_before = USER.objects.count()
        user.soft_delete(updated_by=user)
        self.assertEqual(USER.objects.count(), count_before - 1)

    def test_manager_all_objects_includes_deleted(self):
        user = USER.objects.create_user("deleted2@example.com", "123", role="TCH")
        count_before = USER.all_objects.count()
        user.soft_delete(updated_by=user)
        self.assertEqual(USER.all_objects.count(), count_before)

    def test_create_superuser_with_invalid_staff_flag(self):
        with self.assertRaisesMessage(
            ValueError, "Superuser must have is_staff=True."
        ):
            USER.objects.create_superuser(
                "bad-staff@example.com",
                "badpass",
                role="ADM",
                is_staff=False,
            )

    def test_create_superuser_with_invalid_superuser_flag(self):
        with self.assertRaisesMessage(
            ValueError, "Superuser must have is_superuser=True."
        ):
            USER.objects.create_superuser(
                "bad-superuser@example.com",
                "badpass",
                role="ADM",
                is_superuser=False,
            )

    def test_create_user_with_missing_email(self):
        with self.assertRaisesMessage(
            ValueError, "The given email must be set"
        ):
            USER.objects.create_user("", "password", role="TCH")


class AccountManagementCommandEdgeCasesTestCase(TestCase):
    def setUp(self):
        self.admin = USER.objects.create_user("admin@example.com", "123", role="ADM")

    def test_create_user_with_invalid_email(self):
        self.assertRaisesMessage(
            CommandError,
            "Invalid email address!",
            call_command,
            "create_user",
            "-e",
            "invalid-email",
            "-p",
            "te$t1234",
            "-r",
            "TCH",
        )

    def test_create_user_with_short_password(self):
        out = StringIO()
        call_command(
            "create_user",
            "-e",
            "short@example.com",
            "-p",
            "ab",
            "-r",
            "TCH",
            stdout=out,
        )
        user = USER.objects.get(email="short@example.com")
        self.assertTrue(user.check_password("ab"))
