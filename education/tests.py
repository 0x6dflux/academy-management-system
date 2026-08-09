from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from account.models import User
from education.models import School, SchoolContactPerson
from education.views import HomeAPIView
from system.utils import EndpointTestsMixin, ModelTestsMixin

USER = User


class EducationModelsTestCases(TestCase, ModelTestsMixin):
    def setUp(self) -> None:
        self.admin = USER.objects.create_user(
            "admin-test@example.com",
            "123",
            role="ADM",
        )

    def test_school(self) -> None:
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
        }

        self.run_model_equal_assertions(School, school_data, school_data["name"])

    def test_school_contact_person(self) -> None:
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }
        school_instance = School.objects.create(**school_data)

        school_contact_person_data = {
            "school_id": school_instance.id,
            "first_name": "Majid",
            "last_name": "Dehghan",
            "school_role": 2,
            "mobile_number": "0989191234567",
            "landline_extension_number": 245,
        }

        self.run_model_equal_assertions(
            SchoolContactPerson,
            school_contact_person_data,
            f"{school_contact_person_data['first_name']} {school_contact_person_data['last_name']}",
        )


class EducationEndpointsTestCases(TestCase, EndpointTestsMixin):
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
        self.client = APIClient()

    def test_education_home_rejects_unsupported_methods(self):
        url = reverse("education:home")
        view_class = HomeAPIView

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

    def test_education_home_permissions(self):
        method = "get"
        url = reverse("education:home")
        view_class = HomeAPIView

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
            f"Anonymous user got access with {method}!",
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

        response = self.run_server_with_APIRequestFactory(
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

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            {},
            view_class,
            authentication=True,
            user=self.education_officer,
        )
        self.assertEqual(
            response.status_code,
            200,
            f"{self.education_officer} did not get access with {method}",
        )

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
            200,
            f"{self.admin} did not get access with {method}",
        )

    def test_education_home(self):
        method = "get"
        url = reverse("education:home")
        body = {}
        view_class = HomeAPIView

        response = self.run_server_with_APIRequestFactory(
            method,
            url,
            body,
            view_class,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(response.status_code, 200, "Response status code is not 200!")
        self.assertEqual(response.data["status"], 200, "Status is not 200!")
        self.assertEqual(
            response.data["message"],
            "Education API",
            "Inconsistent message!",
        )

    def test_education_school_rejects_unsupported_methods(self):
        urls = (
            reverse("education:school-list"),
            reverse("education:school-detail", kwargs={"pk": 1}),
        )
        body = {}

        for url in urls:
            for method in {"head", "options"}:
                response = self.run_server_with_APIClient(
                    method,
                    url,
                    body,
                    authentication=True,
                    user=self.admin,
                )

                self.assertEqual(
                    response.status_code,
                    405,
                    f"{self.admin} got access with {method}!",
                )

    def test_education_school_contact_person_rejects_unsupported_methods(self):
        urls = (
            reverse("education:schoolcontactperson-list"),
            reverse("education:schoolcontactperson-detail", kwargs={"pk": 1}),
        )
        body = {}

        for url in urls:
            for method in {"head", "options"}:
                response = self.run_server_with_APIClient(
                    method,
                    url,
                    body,
                    authentication=True,
                    user=self.admin,
                )

                self.assertEqual(
                    response.status_code,
                    405,
                    f"{self.admin} got access with {method}!",
                )

    def test_education_school_permissions(self):
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }
        school_instance = School.objects.create(**school_data)

        method = "get"
        urls = (
            reverse("education:school-list"),
            reverse("education:school-detail", kwargs={"pk": school_instance.id}),
        )
        body = {}

        for url in urls:
            # anonymous user
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
            )
            self.assertEqual(
                response.status_code,
                401,
                f"Anonymous user got access with {method}!",
            )

            # authenticated user
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.finance_officer,
            )
            self.assertEqual(
                response.status_code,
                403,
                f"{self.finance_officer} got access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.teacher,
            )
            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.education_officer,
            )
            self.assertEqual(
                response.status_code,
                200,
                f"{self.education_officer} did not get access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.admin,
            )
            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}",
            )

    def test_education_school_contact_person_permissions(self):
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }
        school_instance = School.objects.create(**school_data)

        school_contact_person_data = {
            "school_id": school_instance.id,
            "first_name": "Majid",
            "last_name": "Dehghan",
            "school_role": 2,
            "mobile_number": "0989191234567",
            "landline_extension_number": 245,
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }
        school_contact_person_instance = SchoolContactPerson.objects.create(
            **school_contact_person_data
        )

        method = "get"
        urls = (
            reverse("education:schoolcontactperson-list"),
            reverse(
                "education:schoolcontactperson-detail",
                kwargs={"pk": school_contact_person_instance.id},
            ),
        )
        body = {}

        for url in urls:
            # anonymous user
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
            )
            self.assertEqual(
                response.status_code,
                401,
                f"Anonymous user got access with {method}!",
            )

            # authenticated user
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.finance_officer,
            )
            self.assertEqual(
                response.status_code,
                403,
                f"{self.finance_officer} got access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.teacher,
            )
            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.education_officer,
            )
            self.assertEqual(
                response.status_code,
                200,
                f"{self.education_officer} did not get access with {method}",
            )

            response = self.run_server_with_APIClient(
                method,
                url,
                {},
                authentication=True,
                user=self.admin,
            )
            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}",
            )

    def test_education_school(self):
        # testing POST
        method = "post"
        url = reverse("education:school-list")
        body = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
        }

        response = self.run_server_with_APIClient(
            method,
            url,
            body,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            201,
            "Invalid POST response status_code!",
        )

        self.assertEqual(response.data["status"], 201, "Invalid POST response status!")

        response.data["result"].pop("id")
        response.data["result"].pop("serial_number")
        response.data["result"].pop("contact_people")
        self.assertEqual(response.data["result"], body, "Invalid POST response result!")

        # testing GET (list)
        method = "get"

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid GET response status_code!",
        )

        self.assertEqual(response.data["status"], 200, "Invalid GET response status!")

        school_instance_id = response.data["results"][0].pop("id")
        response.data["results"][0].pop("serial_number")
        response.data["results"][0].pop("contact_people")
        self.assertEqual(
            response.data["results"][0],
            body,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"
        url = reverse("education:school-detail", kwargs={"pk": school_instance_id})

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid GET-retrieve response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid GET-retrieve response status!",
        )

        response.data["result"].pop("id")
        response.data["result"].pop("serial_number")
        response.data["result"].pop("contact_people")
        self.assertEqual(
            response.data["result"],
            body,
            "Invalid GET-retrieve response results!",
        )

        # testing PUT
        method = "put"

        response = self.run_server_with_APIClient(
            method,
            url,
            body,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PUT response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid PUT response status!",
        )

        response.data["result"].pop("id")
        response.data["result"].pop("serial_number")
        response.data["result"].pop("contact_people")
        self.assertEqual(
            response.data["result"],
            body,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {"name": "RAJAEI"},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid PATCH response status!",
        )

        response.data["result"].pop("id")
        response.data["result"].pop("serial_number")
        response.data["result"].pop("contact_people")
        body["name"] = "RAJAEI"
        self.assertEqual(
            response.data["result"],
            body,
            "Invalid PATCH response results!",
        )

        # testing DELETE
        method = "delete"

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            204,
            "Invalid PATCH response status_code!",
        )

    def test_education_school_contact_person(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:schoolcontactperson-list")

        body = {
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "school_role": 1,
            "mobile_number": "0989191234567",
            "landline_extension_number": 123,
            "school_id": school.id,
        }

        expected_response = {
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "school_role": 1,
            "mobile_number": "0989191234567",
            "landline_extension_number": 123,
            "school": str(school),
        }

        # testing POST
        method = "post"

        response = self.run_server_with_APIClient(
            method,
            url,
            body,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            201,
            "Invalid POST response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            201,
            "Invalid POST response status!",
        )

        response.data["result"].pop("id")

        self.assertEqual(
            response.data["result"],
            expected_response,
            "Invalid POST response result!",
        )

        # testing GET (list)
        method = "get"

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid GET response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid GET response status!",
        )

        contact_person_id = response.data["results"][0].pop("id")

        self.assertEqual(
            response.data["results"][0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:schoolcontactperson-detail",
            kwargs={"pk": contact_person_id},
        )

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid GET-retrieve response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid GET-retrieve response status!",
        )

        response.data["result"].pop("id")

        self.assertEqual(
            response.data["result"],
            expected_response,
            "Invalid GET-retrieve response results!",
        )

        # testing PUT
        method = "put"

        response = self.run_server_with_APIClient(
            method,
            url,
            body,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PUT response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid PUT response status!",
        )

        response.data["result"].pop("id")

        self.assertEqual(
            response.data["result"],
            expected_response,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {"first_name": "Mohammad"},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        self.assertEqual(
            response.data["status"],
            200,
            "Invalid PATCH response status!",
        )

        response.data["result"].pop("id")

        expected_response["first_name"] = "Mohammad"

        self.assertEqual(
            response.data["result"],
            expected_response,
            "Invalid PATCH response results!",
        )

        # testing DELETE
        method = "delete"

        response = self.run_server_with_APIClient(
            method,
            url,
            {},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            204,
            "Invalid DELETE response status_code!",
        )
