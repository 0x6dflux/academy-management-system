# mypy: disable-error-code="attr-defined"

"""Tests for substitute-teacher validation, persistence, and integration."""

from datetime import date, time
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import serializers
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
)
from rest_framework.test import APIClient

from account.models import TeacherProfile, User
from education.models import (
    Course,
    Report,
    School,
    Semester,
    Session,
    TeacherCourse,
)
from education.serializers import (
    SubstituteTeacherSerializer,
    TeacherCourseModelSerializer,
)


class SubstituteTeacherTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            "substitute-admin@example.com",
            "admin-password",
            role=User.RoleChoices.ADMIN,
        )
        cls.education_officer = User.objects.create_user(
            "substitute-edo@example.com",
            "education-password",
            role=User.RoleChoices.EDUCATION_OFFICER,
        )
        cls.finance_officer = User.objects.create_user(
            "substitute-fio@example.com",
            "finance-password",
            role=User.RoleChoices.FINANCE_OFFICER,
        )
        cls.original_teacher = User.objects.create_user(
            "substitute-original@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        cls.substitute_teacher = User.objects.create_user(
            "substitute-replacement@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        cls.third_teacher = User.objects.create_user(
            "substitute-third@example.com",
            "teacher-password",
            role=User.RoleChoices.TEACHER,
        )
        cls.original_profile = cls.create_profile(
            cls.original_teacher,
            first_name="Original",
        )
        cls.substitute_profile = cls.create_profile(
            cls.substitute_teacher,
            first_name="Substitute",
        )
        cls.third_profile = cls.create_profile(
            cls.third_teacher,
            first_name="Third",
        )
        cls.school = School.objects.create(
            name="Substitute Test School",
            email="substitute-school@example.com",
            landline_number="02150000001",
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.semester = Semester.objects.create(
            school=cls.school,
            name="Substitute Test Semester",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            is_summer_semester=False,
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.course = Course.objects.create(
            semester=cls.semester,
            name="Substitute Test Course",
            level=Course.LevelChoices.BASIC,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=cls.admin,
            updated_by=cls.admin,
        )
        cls.session = cls.create_session(date(2026, 10, 15))
        cls.original_assignment = TeacherCourse.objects.create(
            teacher_profile=cls.original_profile,
            course=cls.course,
            started_at=date(2026, 10, 5),
            ended_at=date(2026, 10, 25),
            created_by=cls.admin,
            updated_by=cls.admin,
        )

    @classmethod
    def create_profile(
        cls,
        user: User,
        *,
        first_name: str,
    ) -> TeacherProfile:
        return TeacherProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name="Teacher",
            mobile_number=f"0915{user.pk:07d}",
            landline_number=f"0215{user.pk:07d}",
            created_by=cls.admin,
            updated_by=cls.admin,
        )

    @classmethod
    def create_session(cls, session_date: date) -> Session:
        return Session.objects.create(
            course=cls.course,
            date=session_date,
            start_time=time(9, 0),
            end_time=time(10, 30),
            created_by=cls.admin,
            updated_by=cls.admin,
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("education:substitute-teacher")

    def substitution_payload(
        self,
        *,
        session: Session | None = None,
        teacher_profile: TeacherProfile | None = None,
    ) -> dict:
        return {
            "session": (session or self.session).pk,
            "teacher_profile": (
                teacher_profile or self.substitute_profile
            ).pk,
        }

    def post_substitution(
        self,
        *,
        user: User | None = None,
        session: Session | None = None,
        teacher_profile: TeacherProfile | None = None,
    ):
        self.client.force_authenticate(user or self.education_officer)
        return self.client.post(
            self.url,
            self.substitution_payload(
                session=session,
                teacher_profile=teacher_profile,
            ),
        )

    def create_report(self, session: Session | None = None) -> Report:
        return Report.objects.create(
            session=session or self.session,
            teacher_profile=self.original_profile,
            tutorial_summary="A report already exists.",
            number_of_attendees=10,
            number_of_absentees=0,
            is_delayed=False,
            delay_time=0,
            created_by=self.original_teacher,
            updated_by=self.original_teacher,
        )

    def assert_original_assignment_unchanged(self) -> None:
        self.original_assignment.refresh_from_db()
        self.assertFalse(self.original_assignment.is_deleted)
        self.assertEqual(self.original_assignment.started_at, date(2026, 10, 5))
        self.assertEqual(self.original_assignment.ended_at, date(2026, 10, 25))
        self.assertEqual(TeacherCourse.objects.count(), 1)

    def test_serializer_accepts_valid_substitution_and_exposes_assignment(
        self,
    ) -> None:
        serializer = SubstituteTeacherSerializer(data=self.substitution_payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["session"], self.session)
        self.assertEqual(
            serializer.validated_data["teacher_profile"],
            self.substitute_profile,
        )
        self.assertEqual(
            serializer.validated_data["original_assignment"],
            self.original_assignment,
        )

    def test_serializer_rejects_missing_and_invalid_identifiers(self) -> None:
        cases = (
            ({"teacher_profile": self.substitute_profile.pk}, "session"),
            ({"session": self.session.pk}, "teacher_profile"),
            (
                {
                    "session": 999999,
                    "teacher_profile": self.substitute_profile.pk,
                },
                "session",
            ),
            (
                {"session": self.session.pk, "teacher_profile": 999999},
                "teacher_profile",
            ),
        )

        for payload, expected_field in cases:
            with self.subTest(payload=payload):
                serializer = SubstituteTeacherSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(expected_field, serializer.errors)

    def test_serializer_rejects_soft_deleted_session(self) -> None:
        self.session.soft_delete(updated_by=self.admin)
        serializer = SubstituteTeacherSerializer(data=self.substitution_payload())

        self.assertFalse(serializer.is_valid())
        self.assertIn("session", serializer.errors)

    def test_serializer_rejects_soft_deleted_substitute_profile(self) -> None:
        self.substitute_profile.soft_delete(updated_by=self.admin)
        serializer = SubstituteTeacherSerializer(data=self.substitution_payload())

        self.assertFalse(serializer.is_valid())
        self.assertIn("teacher_profile", serializer.errors)

    def test_serializer_rejects_session_without_active_teacher(self) -> None:
        self.original_assignment.soft_delete(updated_by=self.admin)
        serializer = SubstituteTeacherSerializer(data=self.substitution_payload())

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "This course has no teacher assigned on this date!",
            str(serializer.errors),
        )

    def test_serializer_rejects_current_teacher_as_substitute(self) -> None:
        serializer = SubstituteTeacherSerializer(
            data=self.substitution_payload(teacher_profile=self.original_profile)
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "The substitute teacher cannot be the current teacher!",
            str(serializer.errors),
        )

    def test_serializer_rejects_session_with_existing_report(self) -> None:
        self.create_report()
        serializer = SubstituteTeacherSerializer(data=self.substitution_payload())

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "A substitute teacher cannot be assigned after a report has been submitted!",
            str(serializer.errors),
        )

    def test_permission_matrix_rejects_disallowed_users_without_mutation(self) -> None:
        cases = (
            (None, HTTP_401_UNAUTHORIZED),
            (self.original_teacher, HTTP_403_FORBIDDEN),
            (self.finance_officer, HTTP_403_FORBIDDEN),
        )

        for user, expected_status in cases:
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                response = self.client.post(self.url, self.substitution_payload())
                self.assertEqual(response.status_code, expected_status)

        self.assert_original_assignment_unchanged()

    def test_admin_can_substitute_teacher(self) -> None:
        response = self.post_substitution(user=self.admin)

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        substitute_assignment = TeacherCourse.objects.get(
            teacher_profile=self.substitute_profile
        )
        self.assertEqual(response.data["id"], substitute_assignment.pk)

    def test_middle_day_substitution_splits_assignment_into_three_periods(
        self,
    ) -> None:
        response = self.post_substitution()

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        assignments = list(
            TeacherCourse.objects.order_by("started_at").values_list(
                "teacher_profile_id",
                "started_at",
                "ended_at",
            )
        )
        self.assertEqual(
            assignments,
            [
                (
                    self.original_profile.pk,
                    date(2026, 10, 5),
                    date(2026, 10, 14),
                ),
                (
                    self.substitute_profile.pk,
                    date(2026, 10, 15),
                    date(2026, 10, 15),
                ),
                (
                    self.original_profile.pk,
                    date(2026, 10, 16),
                    date(2026, 10, 25),
                ),
            ],
        )

    def test_middle_day_substitution_records_audit_users(self) -> None:
        self.post_substitution()

        original_before = TeacherCourse.objects.get(pk=self.original_assignment.pk)
        new_assignments = TeacherCourse.objects.exclude(pk=self.original_assignment.pk)
        self.assertEqual(original_before.created_by, self.admin)
        self.assertEqual(original_before.updated_by, self.education_officer)
        for assignment in new_assignments:
            self.assertEqual(assignment.created_by, self.education_officer)
            self.assertEqual(assignment.updated_by, self.education_officer)

    def test_first_assignment_day_soft_deletes_original_and_creates_two_periods(
        self,
    ) -> None:
        first_day_session = self.create_session(date(2026, 10, 5))

        response = self.post_substitution(session=first_day_session)

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        deleted_original = TeacherCourse.all_objects.get(
            pk=self.original_assignment.pk
        )
        self.assertTrue(deleted_original.is_deleted)
        self.assertEqual(deleted_original.updated_by, self.education_officer)
        self.assertEqual(
            list(
                TeacherCourse.objects.order_by("started_at").values_list(
                    "teacher_profile_id",
                    "started_at",
                    "ended_at",
                )
            ),
            [
                (
                    self.substitute_profile.pk,
                    date(2026, 10, 5),
                    date(2026, 10, 5),
                ),
                (
                    self.original_profile.pk,
                    date(2026, 10, 6),
                    date(2026, 10, 25),
                ),
            ],
        )

    def test_last_assignment_day_creates_no_trailing_original_period(self) -> None:
        last_day_session = self.create_session(date(2026, 10, 25))

        response = self.post_substitution(session=last_day_session)

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        self.assertEqual(
            list(
                TeacherCourse.objects.order_by("started_at").values_list(
                    "teacher_profile_id",
                    "started_at",
                    "ended_at",
                )
            ),
            [
                (
                    self.original_profile.pk,
                    date(2026, 10, 5),
                    date(2026, 10, 24),
                ),
                (
                    self.substitute_profile.pk,
                    date(2026, 10, 25),
                    date(2026, 10, 25),
                ),
            ],
        )

    def test_single_day_assignment_is_replaced_and_soft_deleted(self) -> None:
        self.original_assignment.started_at = self.session.date
        self.original_assignment.ended_at = self.session.date
        self.original_assignment.save(update_fields=("started_at", "ended_at"))

        response = self.post_substitution()

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        self.assertFalse(
            TeacherCourse.objects.filter(pk=self.original_assignment.pk).exists()
        )
        self.assertTrue(
            TeacherCourse.all_objects.get(pk=self.original_assignment.pk).is_deleted
        )
        active_assignment = TeacherCourse.objects.get()
        self.assertEqual(active_assignment.teacher_profile, self.substitute_profile)
        self.assertEqual(active_assignment.started_at, self.session.date)
        self.assertEqual(active_assignment.ended_at, self.session.date)

    def test_repeated_substitution_replaces_current_substitute_for_that_day(
        self,
    ) -> None:
        first_response = self.post_substitution()
        second_response = self.post_substitution(teacher_profile=self.third_profile)

        self.assertEqual(first_response.status_code, HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, HTTP_201_CREATED)
        self.assertFalse(
            TeacherCourse.objects.filter(
                teacher_profile=self.substitute_profile,
                started_at=self.session.date,
                ended_at=self.session.date,
            ).exists()
        )
        self.assertTrue(
            TeacherCourse.all_objects.filter(
                teacher_profile=self.substitute_profile,
                started_at=self.session.date,
                ended_at=self.session.date,
                is_deleted=True,
            ).exists()
        )
        self.assertTrue(
            TeacherCourse.objects.filter(
                teacher_profile=self.third_profile,
                started_at=self.session.date,
                ended_at=self.session.date,
            ).exists()
        )

    def test_validation_errors_leave_assignment_unchanged(self) -> None:
        self.client.force_authenticate(self.education_officer)
        for payload in (
            self.substitution_payload(teacher_profile=self.original_profile),
            {"session": 999999, "teacher_profile": self.substitute_profile.pk},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload)
                self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        self.assert_original_assignment_unchanged()

    def test_existing_report_returns_400_without_mutating_assignment(self) -> None:
        self.create_report()

        response = self.post_substitution()

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assert_original_assignment_unchanged()

    def test_endpoint_supports_only_post(self) -> None:
        self.client.force_authenticate(self.education_officer)

        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, {})
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_operation_rolls_back_if_later_assignment_save_fails(self) -> None:
        real_save = TeacherCourseModelSerializer.save
        call_count = 0

        def fail_second_save(serializer, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise serializers.ValidationError("Forced reassignment failure.")
            return real_save(serializer, **kwargs)

        with patch.object(
            TeacherCourseModelSerializer,
            "save",
            new=fail_second_save,
        ):
            response = self.post_substitution()

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assert_original_assignment_unchanged()

    def test_substitute_teacher_can_submit_report_for_substituted_session(
        self,
    ) -> None:
        substitution_response = self.post_substitution()
        self.assertEqual(substitution_response.status_code, HTTP_201_CREATED)
        self.client.force_authenticate(self.substitute_teacher)

        response = self.client.post(
            reverse("education:report-list"),
            {
                "session_id": self.session.pk,
                "tutorial_summary": "Substitute teacher report",
                "number_of_attendees": 10,
                "number_of_absentees": 0,
            },
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED, response.data)
        report = Report.objects.get(session=self.session)
        self.assertEqual(report.teacher_profile, self.substitute_profile)

    def test_original_teacher_cannot_submit_report_for_substituted_session(
        self,
    ) -> None:
        substitution_response = self.post_substitution()
        self.assertEqual(substitution_response.status_code, HTTP_201_CREATED)
        self.client.force_authenticate(self.original_teacher)

        response = self.client.post(
            reverse("education:report-list"),
            {
                "session_id": self.session.pk,
                "tutorial_summary": "Original teacher should not report",
                "number_of_attendees": 10,
                "number_of_absentees": 0,
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("session_id", response.data)
        self.assertIn(
            "You can only submit reports for sessions assigned to you.",
            str(response.data["session_id"]),
        )
        self.assertFalse(Report.objects.filter(session=self.session).exists())
