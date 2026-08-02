from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from education.views import HomeAPIView

if TYPE_CHECKING:
    from account.models import User


USER: User = get_user_model()  # type: ignore


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
        self.teacher = USER.objects.create_user(
            username="mhd_TCH",
            password="3-tch",
            role="TCH",
        )

        # =================
        # setup the request
        # =================
        self.http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
        self.factory = APIRequestFactory()

    def test_education_home_rejects_unsupported_methods(self):
        url = reverse("education:home")
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
        url = reverse("education:home")
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
            user=self.finance_officer,
        )
        self.assertEqual(
            response.status_code,
            403,
            f"{self.finance_officer} got access with {method}",
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
            user=self.education_officer,
        )
        self.assertEqual(
            response.status_code,
            200,
            f"{self.education_officer} did not get access with {method}",
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
