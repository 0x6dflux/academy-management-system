from typing import Any

from django.core.exceptions import ValidationError
from django.core.management import CommandError, CommandParser
from django.core.management.base import BaseCommand
from django.core.validators import validate_email

from account.models import User

USER = User
# since this is a project not a framework and it is not going to be extended,
# the `User` model is directly imported - `get_user_model()` has been removed!


class Command(BaseCommand):
    help = "Creates a new user"

    def add_arguments(self, parser: CommandParser) -> None:
        option: dict[str, Any] = {"type": str, "required": True}
        role_option: dict[str, Any] = {**option, "choices": USER.RoleChoices}

        parser.add_argument("-e", "--email", help="Set the email", **option)
        parser.add_argument("-p", "--password", help="Set the password", **option)
        parser.add_argument("-r", "--role", help="Set the role", **role_option)

    def handle(self, *args, **options) -> None:
        # [hint] a `try-except` block was used to handle the exceptions, but,
        #        this made writing tests difficult. instead, raising exceptions
        #        with `if` statements was chosen

        # [option] Authentication and authorization for this command
        # [todo] user shall input their username and password
        # [todo] if the user is not ADMIN, raise exception `PermissionDenied`
        # [todo] get the admin user by username, `USER.objects.get(username=username)`
        # [hint] with multiple admins, the `MultipleObjectsReturned` exception shall not be
        #        handled, since the username is unique

        if not USER.objects.filter(role=USER.RoleChoices.ADMIN).exists():
            raise CommandError("No user with admin role found!")
            # raising exception is useful in tests

        # default: the first user shall be the ADMIN
        # default: this is the only user with ADMIN role
        # admin = USER.objects.get(role=USER.RoleChoices.ADMIN)
        # [FINAL DECISION] all users are made by admin, so, it is not required to set
        # `created_by` or `updated_by`. this is the reason for changing the `User` model.

        try:
            email = options["email"]
            validate_email(email)
        except ValidationError:
            raise CommandError("Invalid email address!")

        if USER.objects.filter(email=email).exists():
            raise CommandError("Email is not available!")
            # raising exception is useful in tests

        new_user = USER.objects.create_user(
            email,
            options["password"],
            role=options["role"],
        )

        message = f"'{new_user.email}' with 'id={new_user.id}' created successfully."  # type: ignore
        self.stdout.write(self.style.SUCCESS(message))
