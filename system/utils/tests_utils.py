from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.test import force_authenticate
from rest_framework.views import APIView

from account.models import User
from system.models import SerialNumberAbbreviation

USER = User


class ModelTestsMixin:
    """
    In the `setUp` method of your test class, there shall be an attribute
    called `self.admin`. This is required to set the `created_by` and `updated_by`.
    """

    def run_model_equal_assertions(self, model, creation_data, _str_) -> None:
        # creating a new model row in database
        creation_data = {
            **creation_data,
            "created_by_id": self.admin.pk,  # type: ignore
            "updated_by_id": self.admin.pk,  # type: ignore
        }
        creation_result = model.objects.create(**creation_data)

        # preparing expected data
        expected_data = {
            "id": creation_result.id,
            **creation_data,
            "created_at": now().replace(second=0, microsecond=0),
            "updated_at": now().replace(second=0, microsecond=0),
        }

        if hasattr(model, "is_deleted"):
            expected_data["is_deleted"] = False

        if hasattr(SerialNumberAbbreviation, model.__name__.upper()):
            model_abbreviation = getattr(
                SerialNumberAbbreviation,
                model.__name__.upper(),
            )
            serial_digit = 1
            serial_number = f"{model_abbreviation}{serial_digit:04d}"
            expected_data["serial_digit"] = serial_digit
            expected_data["serial_number"] = serial_number

        # testing
        # there shall be only one row in the `education_school` table
        model_instance = model.objects.get(id=creation_result.id)

        for field in model._meta.fields:
            field_name = field.get_attname()

            if field_name in ("created_at", "updated_at"):
                self.assertEqual(  # type: ignore
                    field.value_from_object(model_instance).replace(
                        second=0,
                        microsecond=0,
                    ),
                    expected_data[field_name],
                    f"Inconsistent {model.__name__} {field_name}",
                )
            else:
                self.assertEqual(  # type: ignore
                    field.value_from_object(model_instance),
                    expected_data[field_name],
                    f"Inconsistent {model.__name__} {field_name}!",
                )

        self.assertEqual(  # type: ignore
            str(model_instance),
            _str_,
            "Inconsistent __str__ result!",
        )


class EndpointTestsMixin:
    """
    In the `setUp` method of your test class, there shall be attributes
    representing `self.factory` and `self.client`.
    """

    def run_server_with_APIRequestFactory(
        self,
        method: str,
        url: str,
        body: dict,
        view_class: type[APIView],
        *,
        authentication=False,
        user: User | None = None,
    ) -> Response:
        """This method simulates a server using `APIRequestFactory` and `APIView`."""
        request = getattr(self.factory, method)(url, body)  # type: ignore
        view = view_class.as_view()
        if authentication:
            force_authenticate(request, user)

        return view(request)

    def run_server_with_APIClient(
        self,
        method: str,
        url: str,
        body: dict,
        *,
        authentication=False,
        user: User | None = None,
    ) -> Response:
        """This method simulates a server using `APIClient`."""
        self.client.logout()  # type: ignore
        if authentication:
            self.client.force_authenticate(user)  # type: ignore

        return getattr(self.client, method)(url, body)  # type: ignore
