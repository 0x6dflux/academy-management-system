from django.core.management import CommandParser
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from account.models import User


class Command(BaseCommand):
    help = "Creates a new User"

    def add_arguments(self, parser: CommandParser) -> None:
        option = {"type": str, "required": True}
        role_option = {**option, "choices": User.RoleChoices}

        parser.add_argument("-u", "--username", help="Set the username", **option)  # type: ignore
        parser.add_argument("-p", "--password", help="Set the password", **option)  # type: ignore
        parser.add_argument("-r", "--role", help="Set the role", **role_option)  # type: ignore

    def handle(self, *args, **options) -> None:
        try:
            # [option] Authentication and authorization for this command
            # [todo] user shall input their username and password
            # [todo] if the user is not ADMIN, raise exception `PermissionDenied`
            # [todo] get the admin user by username, `User.objects.get(username=username)`
            # [hint] with multiple admins, the `MultipleObjectsReturned` exception shall not be
            #        handled, since the username is unique

            # default: the first user shall be the ADMIN
            # default: this is the only user with ADMIN role
            admin = User.objects.get(role=User.RoleChoices.ADMIN)

            new_user = User.objects.create_user(
                username=options["username"],
                password=options["password"],
                role=options["role"],
                created_by=admin,
                updated_by=admin,
            )

            message = (
                f"'{new_user.username}' with 'id={new_user.id}' created successfully."  # type: ignore
            )
            self.stdout.write(self.style.SUCCESS(message))

        except User.DoesNotExist as e:
            self.stderr.write(str(e))

        except IntegrityError as e:
            self.stderr.write(str(e))
