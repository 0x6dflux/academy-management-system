from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError, transaction

from finance.models import Wage, WageRate
from finance.serializers import (
    WageCalculationSerializer,
    WageModelSerializer,
    WageRateModelSerializer,
)
from finance.tests.helpers import FinanceTestCase


class WageModelTestCase(FinanceTestCase):
    def test_fields_and_string_representation(self) -> None:
        wage = self.create_wage(
            year=2025,
            month=Wage.MonthChoices.MONTH_02,
            amount=Decimal("123456.78"),
        )

        self.assertEqual(wage.teacher_profile, self.teacher_profile)
        self.assertEqual(wage.year, 2025)
        self.assertEqual(wage.month, Wage.MonthChoices.MONTH_02)
        self.assertEqual(wage.amount, Decimal("123456.78"))
        self.assertEqual(str(wage), "2025-February")

    def test_teacher_year_and_month_are_unique_together(self) -> None:
        self.create_wage(year=2025, month=Wage.MonthChoices.MONTH_01)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_wage(year=2025, month=Wage.MonthChoices.MONTH_01)

    def test_same_period_is_allowed_for_different_teachers(self) -> None:
        self.create_wage(year=2025, month=Wage.MonthChoices.MONTH_01)

        other_wage = self.create_wage(
            teacher_profile=self.other_teacher_profile,
            year=2025,
            month=Wage.MonthChoices.MONTH_01,
        )

        self.assertEqual(Wage.objects.count(), 2)
        self.assertEqual(other_wage.teacher_profile, self.other_teacher_profile)

    def test_amount_cannot_be_negative(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_wage(amount=Decimal("-0.01"))

    def test_zero_amount_is_allowed(self) -> None:
        wage = self.create_wage(amount=Decimal("0.00"))

        self.assertEqual(wage.amount, Decimal("0.00"))

    def test_soft_delete_hides_wage_and_preserves_it_in_all_objects(self) -> None:
        wage = self.create_wage()

        wage.soft_delete(updated_by=self.finance_officer)

        self.assertFalse(Wage.objects.filter(pk=wage.pk).exists())
        deleted_wage = Wage.all_objects.get(pk=wage.pk)
        self.assertTrue(deleted_wage.is_deleted)
        self.assertEqual(deleted_wage.updated_by, self.finance_officer)


class WageRateModelTestCase(FinanceTestCase):
    def test_fields_and_string_representation(self) -> None:
        wage_rate = self.create_wage_rate(amount=Decimal("250000.00"))

        self.assertEqual(wage_rate.semester, self.semester)
        self.assertEqual(wage_rate.teacher_profile, self.teacher_profile)
        self.assertEqual(wage_rate.amount, Decimal("250000.00"))
        self.assertEqual(
            str(wage_rate),
            f"{self.teacher_profile}-{self.semester}",
        )

    def test_active_rate_is_unique_per_teacher_and_semester(self) -> None:
        self.create_wage_rate()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_wage_rate(amount=Decimal("300000.00"))

    def test_rate_must_be_strictly_positive(self) -> None:
        for invalid_amount in (Decimal("0.00"), Decimal("-0.01")):
            with self.subTest(amount=invalid_amount):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_wage_rate(amount=invalid_amount)

    def test_soft_deleted_rate_can_be_replaced(self) -> None:
        old_rate = self.create_wage_rate()
        old_rate.soft_delete(updated_by=self.finance_officer)

        replacement = self.create_wage_rate(amount=Decimal("300000.00"))

        self.assertEqual(replacement.amount, Decimal("300000.00"))
        self.assertEqual(WageRate.objects.count(), 1)
        self.assertEqual(WageRate.all_objects.count(), 2)

    def test_soft_delete_records_modifier_and_hides_rate(self) -> None:
        wage_rate = self.create_wage_rate()

        wage_rate.soft_delete(updated_by=self.finance_officer)

        self.assertFalse(WageRate.objects.filter(pk=wage_rate.pk).exists())
        deleted_rate = WageRate.all_objects.get(pk=wage_rate.pk)
        self.assertTrue(deleted_rate.is_deleted)
        self.assertEqual(deleted_rate.updated_by, self.finance_officer)


class WageSerializerTestCase(FinanceTestCase):
    def test_model_serializer_returns_complete_read_representation(self) -> None:
        wage = self.create_wage(
            year=2025,
            month=Wage.MonthChoices.MONTH_03,
            amount=Decimal("9876.50"),
        )

        self.assertEqual(
            WageModelSerializer(wage).data,
            {
                "id": wage.pk,
                "teacher_profile": self.teacher_profile.pk,
                "year": 2025,
                "month": Wage.MonthChoices.MONTH_03,
                "amount": "9876.50",
            },
        )

    def test_model_serializer_does_not_accept_calculated_fields_as_input(self) -> None:
        serializer = WageModelSerializer(
            data={
                "teacher_profile": self.teacher_profile.pk,
                "year": 2025,
                "month": Wage.MonthChoices.MONTH_01,
                "amount": "1000.00",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    def test_calculation_serializer_accepts_a_completed_month(
        self,
        localdate_mock,
    ) -> None:
        serializer = WageCalculationSerializer(data={"year": 2026, "month": 7})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {"year": 2026, "month": 7})
        self.assertEqual(serializer.data, {})
        localdate_mock.assert_called_once_with()

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    def test_calculation_serializer_rejects_current_and_future_months(
        self,
        localdate_mock,
    ) -> None:
        for payload in (
            {"year": 2026, "month": 8},
            {"year": 2026, "month": 9},
            {"year": 2027, "month": 1},
        ):
            with self.subTest(payload=payload):
                serializer = WageCalculationSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn("non_field_errors", serializer.errors)

    def test_calculation_serializer_rejects_invalid_or_missing_fields(self) -> None:
        for payload, expected_field in (
            ({"year": 2025}, "month"),
            ({"month": 1}, "year"),
            ({"year": 2025, "month": 13}, "month"),
            ({"year": "not-a-year", "month": 1}, "year"),
        ):
            with self.subTest(payload=payload):
                serializer = WageCalculationSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(expected_field, serializer.errors)

    @patch(
        "finance.serializers.wage_serializers.timezone.localdate",
        return_value=date(2026, 8, 26),
    )
    def test_calculation_serializer_rejects_year_outside_python_date_range(
        self,
        localdate_mock,
    ) -> None:
        for invalid_year in (0, 10000):
            with self.subTest(year=invalid_year):
                serializer = WageCalculationSerializer(
                    data={"year": invalid_year, "month": 1}
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("year", serializer.errors)


class WageRateSerializerTestCase(FinanceTestCase):
    def serializer_context(self, user) -> dict:
        return {"request": SimpleNamespace(user=user)}

    def test_create_sets_creator_and_updater_from_request(self) -> None:
        serializer = WageRateModelSerializer(
            data={
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "200000.00",
            },
            context=self.serializer_context(self.finance_officer),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        wage_rate = serializer.save()
        self.assertEqual(wage_rate.created_by, self.finance_officer)
        self.assertEqual(wage_rate.updated_by, self.finance_officer)

    def test_update_changes_only_updater(self) -> None:
        wage_rate = self.create_wage_rate(created_by=self.admin)
        serializer = WageRateModelSerializer(
            wage_rate,
            data={"amount": "250000.00"},
            partial=True,
            context=self.serializer_context(self.finance_officer),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_rate = serializer.save()
        self.assertEqual(updated_rate.amount, Decimal("250000.00"))
        self.assertEqual(updated_rate.created_by, self.admin)
        self.assertEqual(updated_rate.updated_by, self.finance_officer)

    def test_duplicate_active_teacher_semester_is_rejected(self) -> None:
        self.create_wage_rate()
        serializer = WageRateModelSerializer(
            data={
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "250000.00",
            },
            context=self.serializer_context(self.finance_officer),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_replacement_is_valid_after_existing_rate_is_soft_deleted(self) -> None:
        wage_rate = self.create_wage_rate()
        wage_rate.soft_delete(updated_by=self.admin)
        serializer = WageRateModelSerializer(
            data={
                "semester": self.semester.pk,
                "teacher_profile": self.teacher_profile.pk,
                "amount": "250000.00",
            },
            context=self.serializer_context(self.finance_officer),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_positive_amount_is_rejected_before_database_save(self) -> None:
        for invalid_amount in ("0.00", "-0.01"):
            with self.subTest(amount=invalid_amount):
                serializer = WageRateModelSerializer(
                    data={
                        "semester": self.semester.pk,
                        "teacher_profile": self.teacher_profile.pk,
                        "amount": invalid_amount,
                    },
                    context=self.serializer_context(self.finance_officer),
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("amount", serializer.errors)
