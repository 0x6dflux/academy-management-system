from datetime import date, time

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from account.models import TeacherProfile, User
from education.models import (
    Course,
    School,
    SchoolContactPerson,
    Semester,
    Session,
    TeacherCourse,
)
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

    def test_semester(self) -> None:
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        semester_data = {
            "school_id": school.id,
            "name": "First Semester",
            "start_date": date(2026, 9, 23),
            "end_date": date(2027, 1, 20),
            "is_summer_semester": False,
        }

        self.run_model_equal_assertions(Semester, semester_data, semester_data["name"])

    def test_course(self) -> None:
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date=date(2026, 9, 23),
            end_date=date(2027, 1, 20),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        course_data = {
            "semester_id": semester.id,
            "name": "Python Programming",
            "level": Course.LevelChoices.BASIC,
            "start_date": date(2026, 10, 1),
            "end_date": date(2027, 1, 10),
            "sessions_length": Course.SessionLengthChoices.MIN90,
        }

        self.run_model_equal_assertions(Course, course_data, course_data["name"])

    def test_session(self) -> None:
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date=date(2026, 9, 23),
            end_date=date(2027, 1, 20),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        course = Course.objects.create(
            semester_id=semester.id,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date=date(2026, 10, 1),
            end_date=date(2027, 1, 10),
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )

        session_data = {
            "course_id": course.id,
            "date": date(2026, 10, 15),
            "start_time": time(10, 0),
            "end_time": time(11, 30),
        }

        self.run_model_equal_assertions(Session, session_data, "2026-10-15")

    def test_teacher_course(self) -> None:
        teacher_user = USER.objects.create_user("tch@google.com", "123", role="TCH")
        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user,
            first_name="Mahdi",
            last_name="Mohammadi",
            mobile_number="0989361234567",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date=date(2026, 9, 23),
            end_date=date(2027, 1, 20),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )
        course = Course.objects.create(
            semester_id=semester.id,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date=date(2026, 10, 1),
            end_date=date(2027, 1, 10),
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )

        teacher_course_data = {
            "teacher_profile_id": teacher_profile.id,
            "course_id": course.id,
            "started_at": date(2026, 10, 5),
            "ended_at": date(2026, 12, 20),
        }

        self.run_model_equal_assertions(
            TeacherCourse,
            teacher_course_data,
            f"{teacher_profile}-{course}",
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
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Mahdi",
            last_name="Mohammadi",
            mobile_number="0989361234567",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.teacher2 = USER.objects.create_user(
            "TCH2@example.com",
            "3-tch",
            role="TCH",
        )
        self.teacher_profile2 = TeacherProfile.objects.create(
            user=self.teacher2,
            first_name="Mahdi",
            last_name="Mohammadi",
            mobile_number="0989361234567",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
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
            reverse("education:school-contact-person-list"),
            reverse("education:school-contact-person-detail", kwargs={"pk": 1}),
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
            reverse("education:school-contact-person-list"),
            reverse(
                "education:school-contact-person-detail",
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

        response.data.pop("id")
        response.data.pop("serial_number")
        response.data.pop("contact_people")
        self.assertEqual(response.data, body, "Invalid POST response result!")

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

        school_instance_id = response.data[0].pop("id")
        response.data[0].pop("serial_number")
        response.data[0].pop("contact_people")
        self.assertEqual(
            response.data[0],
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

        response.data.pop("id")
        response.data.pop("serial_number")
        response.data.pop("contact_people")
        self.assertEqual(
            response.data,
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

        response.data.pop("id")
        response.data.pop("serial_number")
        response.data.pop("contact_people")
        self.assertEqual(
            response.data,
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

        response.data.pop("id")
        response.data.pop("serial_number")
        response.data.pop("contact_people")
        body["name"] = "RAJAEI"
        self.assertEqual(
            response.data,
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

        self.assertFalse(
            School.objects.filter(id=school_instance_id).exists(),
            "School item is not soft deleted!",
        )
        self.assertTrue(
            School.all_objects.filter(id=school_instance_id).exists(),
            "School item is hard deleted!",
        )

    def test_education_school_contact_person(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:school-contact-person-list")

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

        response.data.pop("id")

        self.assertEqual(
            response.data,
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

        contact_person_id = response.data[0].pop("id")

        self.assertEqual(
            response.data[0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:school-contact-person-detail",
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

        response.data.pop("id")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")

        expected_response["first_name"] = "Mohammad"

        self.assertEqual(
            response.data,
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

        self.assertFalse(
            SchoolContactPerson.objects.filter(id=contact_person_id).exists(),
            "SchoolContactPerson item is not soft deleted!",
        )
        self.assertTrue(
            SchoolContactPerson.all_objects.filter(id=contact_person_id).exists(),
            "SchoolContactPerson item is hard deleted!",
        )

    def test_education_semester_rejects_unsupported_methods(self):
        urls = (
            reverse("education:semester-list"),
            reverse("education:semester-detail", kwargs={"pk": 1}),
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

    def test_education_semester_permissions(self):
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }

        school_instance = School.objects.create(**school_data)

        semester_data = {
            "school_id": school_instance.id,
            "name": "First Semester",
            "start_date": "2026-09-23",
            "end_date": "2027-01-20",
            "is_summer_semester": False,
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }

        semester_instance = Semester.objects.create(**semester_data)

        method = "get"

        urls = (
            reverse("education:semester-list"),
            reverse(
                "education:semester-detail",
                kwargs={"pk": semester_instance.id},
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

            # finance officer
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
                f"{self.finance_officer} got access with {method}!",
            )

            # teacher
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.teacher,
            )

            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}!",
            )

            # education officer
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
                f"{self.education_officer} did not get access with {method}!",
            )

            # admin
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.admin,
            )

            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}!",
            )

    def test_education_semester(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:semester-list")

        body = {
            "school_id": school.id,
            "name": "First Semester",
            "start_date": "2026-09-23",
            "end_date": "2027-01-20",
            "is_summer_semester": False,
        }

        expected_response = {
            "school": str(school),
            "name": "First Semester",
            "start_date": "2026-09-23",
            "end_date": "2027-01-20",
            "is_summer_semester": False,
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        semester_instance_id = response.data[0].pop("id")
        response.data[0].pop("serial_number")

        self.assertEqual(
            response.data[0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:semester-detail",
            kwargs={"pk": semester_instance_id},
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
            expected_response,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {"name": "Second Semester"},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        response.data.pop("id")
        response.data.pop("serial_number")

        expected_response["name"] = "Second Semester"

        self.assertEqual(
            response.data,
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

        self.assertFalse(
            Semester.objects.filter(id=semester_instance_id).exists(),
            "Semester item is not soft deleted!",
        )
        self.assertTrue(
            Semester.all_objects.filter(id=semester_instance_id).exists(),
            "Semester item is hard deleted!",
        )

    def test_education_course_rejects_unsupported_methods(self):
        urls = (
            reverse("education:course-list"),
            reverse("education:course-detail", kwargs={"pk": 1}),
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

    def test_education_course_permissions(self):
        school_data = {
            "name": "Rajaei",
            "email": "rajaei@google.com",
            "landline_number": "0982112345678",
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }

        school_instance = School.objects.create(**school_data)

        semester_data = {
            "school_id": school_instance.id,
            "name": "First Semester",
            "start_date": date(2026, 9, 23),
            "end_date": date(2027, 1, 20),
            "is_summer_semester": False,
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }

        semester_instance = Semester.objects.create(**semester_data)

        course_data = {
            "semester_id": semester_instance.id,
            "name": "Python Programming",
            "level": Course.LevelChoices.BASIC,
            "start_date": "2026-10-01",
            "end_date": "2027-01-10",
            "sessions_length": Course.SessionLengthChoices.MIN90,
            "created_by_id": self.admin.pk,
            "updated_by_id": self.admin.pk,
        }

        course_instance = Course.objects.create(**course_data)

        method = "get"

        urls = (
            reverse("education:course-list"),
            reverse(
                "education:course-detail",
                kwargs={"pk": course_instance.id},
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

            # finance officer
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
                f"{self.finance_officer} got access with {method}!",
            )

            # teacher
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.teacher,
            )

            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}!",
            )

            # education officer
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
                f"{self.education_officer} did not get access with {method}!",
            )

            # admin
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.admin,
            )

            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}!",
            )

    def test_education_course(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date=date(2026, 9, 23),
            end_date=date(2027, 1, 20),
            is_summer_semester=False,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:course-list")

        body = {
            "semester_id": semester.id,
            "name": "Python Programming",
            "level": Course.LevelChoices.BASIC,
            "start_date": "2026-10-01",
            "end_date": "2027-01-10",
            "sessions_length": Course.SessionLengthChoices.MIN90,
        }

        expected_response = {
            "semester": str(semester),
            "name": "Python Programming",
            "level": Course.LevelChoices.BASIC,
            "start_date": "2026-10-01",
            "end_date": "2027-01-10",
            "sessions_length": Course.SessionLengthChoices.MIN90,
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        course_instance_id = response.data[0].pop("id")
        response.data[0].pop("serial_number")

        self.assertEqual(
            response.data[0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:course-detail",
            kwargs={"pk": course_instance_id},
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
            expected_response,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {"name": "Advanced Python Programming"},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        response.data.pop("id")
        response.data.pop("serial_number")

        expected_response["name"] = "Advanced Python Programming"

        self.assertEqual(
            response.data,
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

        self.assertFalse(
            Course.objects.filter(id=course_instance_id).exists(),
            "Course item is not soft deleted!",
        )
        self.assertTrue(
            Course.all_objects.filter(id=course_instance_id).exists(),
            "Course item is hard deleted!",
        )

    def test_education_session_rejects_unsupported_methods(self):
        urls = (
            reverse("education:session-list"),
            reverse("education:session-detail", kwargs={"pk": 1}),
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

    def test_education_session_permissions(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )

        session = Session.objects.create(
            course=course,
            date="2026-10-15",
            start_time="10:00:00",
            end_time="11:30:00",
            created_by=self.admin,
            updated_by=self.admin,
        )

        method = "get"

        urls = (
            reverse("education:session-list"),
            reverse(
                "education:session-detail",
                kwargs={"pk": session.id},
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

            # finance officer
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
                f"{self.finance_officer} got access with {method}!",
            )

            # teacher
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.teacher,
            )

            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}!",
            )

            # education officer
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
                f"{self.education_officer} did not get access with {method}!",
            )

            # admin
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.admin,
            )

            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}!",
            )

    def test_education_session(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:session-list")

        body = {
            "course_id": course.id,
            "date": "2026-10-15",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
        }

        expected_response = {
            "course": str(course),
            "date": "2026-10-15",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        session_instance_id = response.data[0].pop("id")
        response.data[0].pop("serial_number")

        self.assertEqual(
            response.data[0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:session-detail",
            kwargs={"pk": session_instance_id},
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")
        response.data.pop("serial_number")

        self.assertEqual(
            response.data,
            expected_response,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {"date": "2026-10-20"},
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        response.data.pop("id")
        response.data.pop("serial_number")

        expected_response["date"] = "2026-10-20"

        self.assertEqual(
            response.data,
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

        self.assertFalse(
            Session.objects.filter(id=session_instance_id).exists(),
            "Session item is not soft deleted!",
        )
        self.assertTrue(
            Session.all_objects.filter(id=session_instance_id).exists(),
            "Session item is hard deleted!",
        )

    def test_education_teacher_course_rejects_unsupported_methods(self):
        urls = (
            reverse("education:teacher-course-list"),
            reverse(
                "education:teacher-course-detail",
                kwargs={"pk": 1},
            ),
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

    def test_education_teacher_course_permissions(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )

        teacher_course = TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=course,
            started_at="2026-10-05",
            ended_at="2026-12-20",
            created_by=self.admin,
            updated_by=self.admin,
        )

        method = "get"

        urls = (
            reverse("education:teacher-course-list"),
            reverse(
                "education:teacher-course-detail",
                kwargs={"pk": teacher_course.id},
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

            # finance officer
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
                f"{self.finance_officer} got access with {method}!",
            )

            # teacher
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.teacher,
            )

            self.assertEqual(
                response.status_code,
                403,
                f"{self.teacher} got access with {method}!",
            )

            # education officer
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
                f"{self.education_officer} did not get access with {method}!",
            )

            # admin
            response = self.run_server_with_APIClient(
                method,
                url,
                body,
                authentication=True,
                user=self.admin,
            )

            self.assertEqual(
                response.status_code,
                200,
                f"{self.admin} did not get access with {method}!",
            )

    def test_education_teacher_course(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:teacher-course-list")

        body = {
            "teacher_profile_id": self.teacher_profile.id,
            "course_id": course.id,
            "started_at": "2026-10-05",
            "ended_at": "2026-12-20",
        }

        expected_response = {
            "teacher_profile": str(self.teacher_profile),
            "course": str(course),
            "started_at": "2026-10-05",
            "ended_at": "2026-12-20",
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

        response.data.pop("id")

        self.assertEqual(
            response.data,
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

        teacher_course_instance_id = response.data[0].pop("id")

        self.assertEqual(
            response.data[0],
            expected_response,
            "Invalid GET response results!",
        )

        # testing GET (retrieve)
        method = "get"

        url = reverse(
            "education:teacher-course-detail",
            kwargs={"pk": teacher_course_instance_id},
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

        response.data.pop("id")

        self.assertEqual(
            response.data,
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

        response.data.pop("id")

        self.assertEqual(
            response.data,
            expected_response,
            "Invalid PUT response results!",
        )

        # testing PATCH
        method = "patch"

        response = self.run_server_with_APIClient(
            method,
            url,
            {
                "started_at": "2026-10-10",
            },
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid PATCH response status_code!",
        )

        response.data.pop("id")

        expected_response["started_at"] = "2026-10-10"

        self.assertEqual(
            response.data,
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

        self.assertFalse(
            TeacherCourse.objects.filter(id=teacher_course_instance_id).exists(),
            "TeacherCourse item is not soft deleted!",
        )
        self.assertTrue(
            TeacherCourse.all_objects.filter(id=teacher_course_instance_id).exists(),
            "TeacherCourse item is hard deleted!",
        )

    def test_education_teacher_course_multiple_teachers(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.education_officer,
            updated_by=self.education_officer,
        )

        url = reverse("education:teacher-course-list")

        body1 = {
            "teacher_profile_id": self.teacher_profile.id,
            "course_id": course.id,
            "started_at": "2026-10-05",
            "ended_at": "2026-11-05",
        }
        body2 = {
            "teacher_profile_id": self.teacher_profile2.id,
            "course_id": course.id,
            "started_at": "2026-11-06",
            "ended_at": "2026-12-05",
        }

        response1 = self.run_server_with_APIClient(
            "post",
            url,
            body1,
            authentication=True,
            user=self.education_officer,
        )
        response2 = self.run_server_with_APIClient(
            "post",
            url,
            body2,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(response1.status_code, 201, "Unsuccessful POST with body1")
        self.assertEqual(response2.status_code, 201, "Unsuccessful POST with body2")

    def test_education_teacher_schedule_rejects_unsupported_methods(self):
        url = reverse("education:teacher-schedule")
        body = {}

        for method in self.http_methods - {"get"}:
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

    def test_education_teacher_schedule_permissions(self):
        url = reverse("education:teacher-schedule")
        body = {}

        # anonymous user
        response = self.run_server_with_APIClient(
            "get",
            url,
            body,
        )

        self.assertEqual(
            response.status_code,
            401,
            "Anonymous user got access with get!",
        )

        # finance officer
        response = self.run_server_with_APIClient(
            "get",
            url,
            body,
            authentication=True,
            user=self.finance_officer,
        )

        self.assertEqual(
            response.status_code,
            403,
            f"{self.finance_officer} got access with get!",
        )

        # education officer
        response = self.run_server_with_APIClient(
            "get",
            url,
            body,
            authentication=True,
            user=self.education_officer,
        )

        self.assertEqual(
            response.status_code,
            403,
            f"{self.education_officer} got access with get!",
        )

        # teacher
        response = self.run_server_with_APIClient(
            "get",
            url,
            body,
            authentication=True,
            user=self.teacher,
        )

        self.assertEqual(
            response.status_code,
            200,
            f"{self.teacher} did not get access with get!",
        )

        # admin
        response = self.run_server_with_APIClient(
            "get",
            url,
            body,
            authentication=True,
            user=self.admin,
        )

        self.assertEqual(
            response.status_code,
            200,
            f"{self.admin} did not get access with get!",
        )

    def test_education_teacher_schedule(self):
        school = School.objects.create(
            name="Rajaei",
            email="rajaei@google.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )

        semester = Semester.objects.create(
            school=school,
            name="First Semester",
            start_date="2026-09-23",
            end_date="2027-01-20",
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        course = Course.objects.create(
            semester=semester,
            name="Python Programming",
            level=Course.LevelChoices.BASIC,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )

        other_course = Course.objects.create(
            semester=semester,
            name="Django Programming",
            level=Course.LevelChoices.ADVANCED,
            start_date="2026-10-01",
            end_date="2027-01-10",
            sessions_length=Course.SessionLengthChoices.MIN120,
            created_by=self.admin,
            updated_by=self.admin,
        )

        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=course,
            started_at="2026-10-05",
            ended_at="2026-12-20",
            created_by=self.admin,
            updated_by=self.admin,
        )

        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile2,
            course=other_course,
            started_at="2026-10-05",
            ended_at="2026-12-20",
            created_by=self.admin,
            updated_by=self.admin,
        )

        Session.objects.create(
            course=course,
            date="2026-10-15",
            start_time="10:00:00",
            end_time="11:30:00",
            created_by=self.admin,
            updated_by=self.admin,
        )

        Session.objects.create(
            course=course,
            date="2026-10-22",
            start_time="10:00:00",
            end_time="11:30:00",
            created_by=self.admin,
            updated_by=self.admin,
        )

        Session.objects.create(
            course=other_course,
            date="2026-10-20",
            start_time="14:00:00",
            end_time="16:00:00",
            created_by=self.admin,
            updated_by=self.admin,
        )

        url = reverse("education:teacher-schedule")

        # =================
        # teacher
        # =================

        response = self.run_server_with_APIClient(
            "get",
            url,
            {},
            authentication=True,
            user=self.teacher,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid teacher response status_code!",
        )

        self.assertEqual(
            len(response.data),
            1,
            "Teacher received invalid number of courses!",
        )

        course_data = response.data[0]

        self.assertEqual(
            course_data["id"],
            course.id,
            "Teacher received an invalid course!",
        )

        self.assertEqual(
            course_data["name"],
            "Python Programming",
            "Invalid course name!",
        )

        self.assertEqual(
            course_data["level"],
            "Basic",
            "Invalid course level!",
        )

        self.assertEqual(
            course_data["start_date"],
            "2026-10-01",
            "Invalid course start_date!",
        )

        self.assertEqual(
            course_data["end_date"],
            "2027-01-10",
            "Invalid course end_date!",
        )

        self.assertEqual(
            course_data["sessions_length"],
            "90 min",
            "Invalid sessions_length!",
        )

        self.assertEqual(
            len(course_data["sessions"]),
            2,
            "Teacher received invalid number of sessions!",
        )

        self.assertEqual(
            course_data["sessions"][0],
            {
                "date": "2026-10-15",
                "start_time": "10:00:00",
                "end_time": "11:30:00",
            },
            "Invalid first session!",
        )

        self.assertEqual(
            course_data["sessions"][1],
            {
                "date": "2026-10-22",
                "start_time": "10:00:00",
                "end_time": "11:30:00",
            },
            "Invalid second session!",
        )

        # teacher must not receive another teacher's course
        returned_course_ids = {course["id"] for course in response.data}

        self.assertNotIn(
            other_course.id,
            returned_course_ids,
            "Teacher received another teacher's course!",
        )

        # =================
        # admin
        # =================

        response = self.run_server_with_APIClient(
            "get",
            url,
            {},
            authentication=True,
            user=self.admin,
        )

        self.assertEqual(
            response.status_code,
            200,
            "Invalid admin response status_code!",
        )

        self.assertEqual(
            len(response.data),
            2,
            "Admin did not receive all courses!",
        )

        returned_course_ids = {course["id"] for course in response.data}

        self.assertIn(
            course.id,
            returned_course_ids,
            "Admin did not receive teacher's course!",
        )

        self.assertIn(
            other_course.id,
            returned_course_ids,
            "Admin did not receive the other course!",
        )
