# mypy: disable-error-code="attr-defined"

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from finance.models import Wage, WageRate
from finance.tests.helpers import FinanceTestCase


class FinanceHomeAPIViewTestCase(FinanceTestCase):
    def test_finance_officer_and_admin_can_access_home(self) -> None:
        url = reverse("finance:home")

        for user in (self.finance_officer, self.admin):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTP_200_OK)
                self.assertEqual(response.data, {"message": "Finance API"})

    def test_anonymous_teacher_and_education_officer_cannot_access_home(self) -> None:
        url = reverse("finance:home")
        cases = (
            (None, HTTP_401_UNAUTHORIZED),
            (self.teacher, HTTP_403_FORBIDDEN),
            (self.education_officer, HTTP_403_FORBIDDEN),
        )

        for user, expected_status in cases:
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_home_rejects_non_get_methods(self) -> None:
        self.client.force_authenticate(self.admin)
        url = reverse("finance:home")

        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, {})
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)


class WageRateViewSetTestCase(FinanceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.list_url = reverse("finance:wage-rate-list")

    def test_list_permission_matrix(self) -> None:
        cases = (
            (None, HTTP_401_UNAUTHORIZED),
            (self.teacher, HTTP_403_FORBIDDEN),
            (self.education_officer, HTTP_403_FORBIDDEN),
            (self.finance_officer, HTTP_200_OK),
            (self.admin, HTTP_200_OK),
        )

        for user, expected_status in cases:
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, expected_status)

    def test_finance_officer_can_create_rate_and_audit_fields_are_set(self) -> None:
        self.client.force_authenticate(self.finance_officer)

        response = self.client.post(
            self.list_url,
            {
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "200000.00",
            },
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        wage_rate = WageRate.objects.get(pk=response.data["id"])
        self.assertEqual(wage_rate.amount, Decimal("200000.00"))
        self.assertEqual(wage_rate.created_by, self.finance_officer)
        self.assertEqual(wage_rate.updated_by, self.finance_officer)

    def test_admin_can_retrieve_rate(self) -> None:
        wage_rate = self.create_wage_rate()
        self.client.force_authenticate(self.admin)

        response = self.client.get(
            reverse("finance:wage-rate-detail", kwargs={"pk": wage_rate.pk})
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["id"], wage_rate.pk)
        self.assertEqual(response.data["amount"], "200000.00")

    def test_put_replaces_rate_and_records_updater(self) -> None:
        wage_rate = self.create_wage_rate(created_by=self.admin)
        self.client.force_authenticate(self.finance_officer)

        response = self.client.put(
            reverse("finance:wage-rate-detail", kwargs={"pk": wage_rate.pk}),
            {
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "225000.00",
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK, response.data)
        wage_rate.refresh_from_db()
        self.assertEqual(wage_rate.amount, Decimal("225000.00"))
        self.assertEqual(wage_rate.created_by, self.admin)
        self.assertEqual(wage_rate.updated_by, self.finance_officer)

    def test_patch_updates_rate_and_records_updater(self) -> None:
        wage_rate = self.create_wage_rate(created_by=self.admin)
        self.client.force_authenticate(self.finance_officer)

        response = self.client.patch(
            reverse("finance:wage-rate-detail", kwargs={"pk": wage_rate.pk}),
            {"amount": "230000.00"},
        )

        self.assertEqual(response.status_code, HTTP_200_OK, response.data)
        wage_rate.refresh_from_db()
        self.assertEqual(wage_rate.amount, Decimal("230000.00"))
        self.assertEqual(wage_rate.created_by, self.admin)
        self.assertEqual(wage_rate.updated_by, self.finance_officer)

    def test_delete_soft_deletes_rate_and_records_deleter(self) -> None:
        wage_rate = self.create_wage_rate(created_by=self.admin)
        detail_url = reverse(
            "finance:wage-rate-detail",
            kwargs={"pk": wage_rate.pk},
        )
        self.client.force_authenticate(self.finance_officer)

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertFalse(WageRate.objects.filter(pk=wage_rate.pk).exists())
        deleted_rate = WageRate.all_objects.get(pk=wage_rate.pk)
        self.assertTrue(deleted_rate.is_deleted)
        self.assertEqual(deleted_rate.updated_by, self.finance_officer)
        self.assertEqual(self.client.get(detail_url).status_code, HTTP_404_NOT_FOUND)

    def test_list_omits_soft_deleted_rates(self) -> None:
        active_rate = self.create_wage_rate()
        deleted_rate = self.create_wage_rate(
            teacher_profile=self.other_teacher_profile,
        )
        deleted_rate.soft_delete(updated_by=self.admin)
        self.client.force_authenticate(self.finance_officer)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {active_rate.pk},
        )

    def test_duplicate_active_rate_returns_validation_error(self) -> None:
        self.create_wage_rate()
        self.client.force_authenticate(self.finance_officer)

        response = self.client.post(
            self.list_url,
            {
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "250000.00",
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_non_positive_rate_returns_validation_error(self) -> None:
        self.client.force_authenticate(self.finance_officer)

        for amount in ("0.00", "-0.01"):
            with self.subTest(amount=amount):
                response = self.client.post(
                    self.list_url,
                    {
                        "semester": self.semester.pk,
                        "teacher_profile": self.teacher_profile.pk,
                        "amount": amount,
                    },
                )
                self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
                self.assertIn("amount", response.data)

        self.assertFalse(WageRate.objects.exists())

    def test_disallowed_roles_cannot_mutate_rates(self) -> None:
        payload = {
            "semester": self.semester.pk,
            "teacher_profile": self.teacher_profile.pk,
            "amount": "200000.00",
        }

        for user, expected_status in (
            (None, HTTP_401_UNAUTHORIZED),
            (self.teacher, HTTP_403_FORBIDDEN),
            (self.education_officer, HTTP_403_FORBIDDEN),
        ):
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.post(self.list_url, payload)
                self.assertEqual(response.status_code, expected_status)


class WageReadOnlyViewSetTestCase(FinanceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.list_url = reverse("finance:wage-list")
        self.own_wage = self.create_wage()
        self.other_wage = self.create_wage(
            teacher_profile=self.other_teacher_profile,
        )

    def test_teacher_list_contains_only_own_wages(self) -> None:
        self.client.force_authenticate(self.teacher)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {self.own_wage.pk},
        )

    def test_teacher_can_retrieve_own_wage_but_not_another_teachers(self) -> None:
        self.client.force_authenticate(self.teacher)
        own_url = reverse("finance:wage-detail", kwargs={"pk": self.own_wage.pk})
        other_url = reverse(
            "finance:wage-detail",
            kwargs={"pk": self.other_wage.pk},
        )

        self.assertEqual(self.client.get(own_url).status_code, HTTP_200_OK)
        self.assertEqual(self.client.get(other_url).status_code, HTTP_404_NOT_FOUND)

    def test_finance_officer_and_admin_can_list_all_wages(self) -> None:
        for user in (self.finance_officer, self.admin):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user)
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, HTTP_200_OK)
                self.assertEqual(
                    {item["id"] for item in response.data},
                    {self.own_wage.pk, self.other_wage.pk},
                )

    def test_anonymous_and_education_officer_cannot_list_wages(self) -> None:
        for user, expected_status in (
            (None, HTTP_401_UNAUTHORIZED),
            (self.education_officer, HTTP_403_FORBIDDEN),
        ):
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, expected_status)

    def test_soft_deleted_wages_are_not_returned(self) -> None:
        self.own_wage.soft_delete(updated_by=self.admin)
        self.client.force_authenticate(self.finance_officer)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {self.other_wage.pk},
        )

    def test_wage_endpoint_rejects_write_methods(self) -> None:
        self.client.force_authenticate(self.admin)
        detail_url = reverse(
            "finance:wage-detail",
            kwargs={"pk": self.own_wage.pk},
        )

        self.assertEqual(
            self.client.post(self.list_url, {}).status_code,
            HTTP_405_METHOD_NOT_ALLOWED,
        )
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(detail_url, {})
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)


class WageCalculationAPIViewTestCase(FinanceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("finance:wage-calculation")
        self.completed_month_payload = {"year": 2026, "month": 7}

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    @patch("finance.views.wage_view.WageService")
    def test_finance_officer_can_calculate_wages(
        self,
        wage_service_mock,
        localdate_mock,
    ) -> None:
        self.client.force_authenticate(self.finance_officer)

        response = self.client.post(self.url, self.completed_month_payload)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"message": "All wages have been calculated."},
        )
        wage_service_mock.assert_called_once_with(
            2026,
            7,
            self.finance_officer,
        )
        wage_service_mock.return_value.calculate_wages.assert_called_once_with()

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    @patch("finance.views.wage_view.WageService")
    def test_admin_can_calculate_wages(
        self,
        wage_service_mock,
        localdate_mock,
    ) -> None:
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.url, self.completed_month_payload)

        self.assertEqual(response.status_code, HTTP_200_OK)
        wage_service_mock.assert_called_once_with(2026, 7, self.admin)

    @patch("finance.views.wage_view.WageService")
    def test_unauthorized_users_cannot_calculate_wages(
        self,
        wage_service_mock,
    ) -> None:
        for user, expected_status in (
            (None, HTTP_401_UNAUTHORIZED),
            (self.teacher, HTTP_403_FORBIDDEN),
            (self.education_officer, HTTP_403_FORBIDDEN),
        ):
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.post(self.url, self.completed_month_payload)
                self.assertEqual(response.status_code, expected_status)

        wage_service_mock.assert_not_called()

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    @patch("finance.views.wage_view.WageService")
    def test_invalid_payload_returns_400_without_calling_service(
        self,
        wage_service_mock,
        localdate_mock,
    ) -> None:
        self.client.force_authenticate(self.finance_officer)

        for payload in (
            {},
            {"year": 2026, "month": 8},
            {"year": 2026, "month": 13},
            {"year": "invalid", "month": 7},
            {"year": 0, "month": 7},
            {"year": 10000, "month": 7},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload)
                self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        wage_service_mock.assert_not_called()

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    @patch("finance.views.wage_view.WageService")
    def test_service_validation_error_is_returned_as_400(
        self,
        wage_service_mock,
        localdate_mock,
    ) -> None:
        wage_service_mock.return_value.calculate_wages.side_effect = ValidationError(
            "There are reports which are not reviewed!"
        )
        self.client.force_authenticate(self.finance_officer)

        response = self.client.post(self.url, self.completed_month_payload)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            ["There are reports which are not reviewed!"],
        )

    def test_get_is_not_supported(self) -> None:
        self.client.force_authenticate(self.finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
