from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

# Create your tests here.

if TYPE_CHECKING:
    from account.models import User


USER: User = get_user_model()  # type: ignore


class AccountTestCase(TestCase):
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
