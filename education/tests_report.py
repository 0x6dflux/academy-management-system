from datetime import datetime, time, timedelta
from typing import Any
from unittest.mock import patch

import pytz
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from account.models import TeacherProfile, User
from config.settings import TIME_ZONE
from education.models import (
    Course,
    Report,
    ReportHistory,
    School,
    Semester,
    Session,
    TeacherCourse,
)
from education.serializers import ReportSubmissionWriteOnlyModelSerializer
from system.utils import EndpointTestsMixin

USER = User


class ReportLifecycleAPITestCase(TestCase, EndpointTestsMixin):
    def setUp(self) -> None:
        # ==================
        # setup the database
        # ==================
        self.admin = USER.objects.create_user(
            "ADM@example.com",
            "0@dmin",
            role=USER.RoleChoices.ADMIN,
        )
        self.education_officer = USER.objects.create_user(
            "EDO@example.com",
            "1/edo",
            role=USER.RoleChoices.EDUCATION_OFFICER,
        )
        self.finance_officer = USER.objects.create_user(
            "FIO@example.com",
            "4/fio",
            role=USER.RoleChoices.FINANCE_OFFICER,
        )
        self.teacher = USER.objects.create_user(
            "TCH1@example.com",
            "2-tch",
            role=USER.RoleChoices.TEACHER,
        )
        self.teacher2 = USER.objects.create_user(
            "TCH2@example.com",
            "3-tch",
            role=USER.RoleChoices.TEACHER,
        )

        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Amir",
            last_name="Ahmadi",
            mobile_number="091200000001",
            landline_number="02130000001",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.teacher_profile2 = TeacherProfile.objects.create(
            user=self.teacher2,
            first_name="Sara",
            last_name="Rostami",
            mobile_number="091200000002",
            landline_number="02130000002",
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.school = School.objects.create(
            name="Rajaei",
            email="rajaei@school.com",
            landline_number="0211234567",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.other_school = School.objects.create(
            name="Pandi",
            email="pandi@school.com",
            landline_number="0217654321",
            created_by=self.admin,
            updated_by=self.admin,
        )

        today = timezone.now().date()
        self.semester = Semester.objects.create(
            school=self.school,
            name="Fall",
            start_date=today - timedelta(days=120),
            end_date=today + timedelta(days=120),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.other_semester = Semester.objects.create(
            school=self.other_school,
            name="Spring",
            start_date=today - timedelta(days=120),
            end_date=today + timedelta(days=120),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.course = Course.objects.create(
            semester=self.semester,
            name="Python Fundamentals",
            level=Course.LevelChoices.BASIC,
            start_date=today - timedelta(days=90),
            end_date=today + timedelta(days=90),
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.other_course = Course.objects.create(
            semester=self.other_semester,
            name="Python Advanced",
            level=Course.LevelChoices.ADVANCED,
            start_date=today - timedelta(days=90),
            end_date=today + timedelta(days=90),
            sessions_length=Course.SessionLengthChoices.MIN120,
            created_by=self.admin,
            updated_by=self.admin,
        )

        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=self.course,
            started_at=today - timedelta(days=45),
            ended_at=today + timedelta(days=45),
            created_by=self.admin,
            updated_by=self.admin,
        )
        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile2,
            course=self.other_course,
            started_at=today - timedelta(days=45),
            ended_at=today + timedelta(days=45),
            created_by=self.admin,
            updated_by=self.admin,
        )

        # =================
        # setup request tools
        # =================
        self.client = APIClient()
        self.local_tz = pytz.timezone(TIME_ZONE)
        self.report_url = reverse("education:report-list")
        self.report_history_url = reverse("education:report-history-list")
        self.bulk_approval_url = reverse("education:report-bulk-approval")
        self.teacher_report_stat_url = reverse("education:teacher-report-stat")

    def _session_payload_relative(self, *, hours_before_end: int) -> dict[str, Any]:
        """
        Build a safe session payload around now using local timezone.

        The session end time is guaranteed to be `hours_before_end` hours before now
        in the application time zone.
        """

        end_dt = timezone.now().astimezone(self.local_tz) - timedelta(
            hours=hours_before_end
        )
        start_dt = end_dt - timedelta(hours=1)

        return {
            "date": end_dt.date(),
            "start_time": datetime(
                2000, 1, 1, hour=start_dt.hour, minute=start_dt.minute
            ).time(),
            "end_time": datetime(
                2000, 1, 1, hour=end_dt.hour, minute=end_dt.minute
            ).time(),
        }

    def _session_payload_on_date(
        self,
        session_date: datetime.date,
        *,
        start_time: time = time(9, 0),
        end_time: time = time(10, 30),
    ) -> dict[str, Any]:
        return {
            "date": session_date,
            "start_time": start_time,
            "end_time": end_time,
        }

    def _create_session(self, *, course: Course, **time_kwargs) -> Session:
        if "hours_before_end" in time_kwargs:
            session_payload = self._session_payload_relative(**time_kwargs)  # type: ignore[arg-type]
        else:
            session_payload = self._session_payload_on_date(
                session_date=time_kwargs["date"],  # type: ignore[index]
                start_time=time_kwargs.get("start_time", time(9, 0)),
                end_time=time_kwargs.get("end_time", time(10, 0)),
            )

        return Session.objects.create(
            course=course,
            date=session_payload["date"],
            start_time=session_payload["start_time"],
            end_time=session_payload["end_time"],
            created_by=self.admin,
            updated_by=self.admin,
        )

    def _create_report_payload(
        self,
        session_id: int,
        *,
        summary: str = "A short lesson about conditionals.",
        attendees: int = 10,
        absentees: int = 2,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "tutorial_summary": summary,
            "number_of_attendees": attendees,
            "number_of_absentees": absentees,
        }

    def _submit_report(
        self,
        user,
        session: Session,
        payload: dict[str, Any] | None = None,
    ):
        payload = payload or self._create_report_payload(session.id)
        self.client.force_authenticate(user=user)
        return self.client.post(self.report_url, payload)

    def _edit_report(
        self,
        user,
        report_id: int,
        payload: dict[str, Any],
    ):
        self.client.force_authenticate(user=user)
        return self.client.patch(
            reverse("education:report-detail", kwargs={"pk": report_id}),
            payload,
        )

    def _review_report(
        self,
        user,
        report: Report,
        *,
        is_approved: bool,
        description: str,
    ):
        self.client.force_authenticate(user=user)
        payload = {
            "report": report.id,
            "is_approved": is_approved,
            "description": description,
        }
        return self.client.post(self.report_url, payload)

    def _latest_history_change(self, report: Report) -> int:
        return int(
            ReportHistory.objects.filter(report=report).order_by("-id").first().change
        )  # type: ignore[union-attr]

    def test_report_permissions(self) -> None:
        self.assertEqual(self.client.get(self.report_url).status_code, 401)
        self.assertEqual(self.client.post(self.report_url, {}).status_code, 401)

        self.client.force_authenticate(self.finance_officer)
        self.assertEqual(self.client.get(self.report_url).status_code, 403)
        self.assertEqual(self.client.post(self.report_url, {}).status_code, 403)

        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.client.get(self.report_url).status_code, 200)

        self.client.force_authenticate(self.education_officer)
        self.assertEqual(self.client.get(self.report_url).status_code, 200)

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.report_url).status_code, 200)

    def test_report_rejects_unsupported_methods(self) -> None:
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.report_url).status_code, 405)
        self.assertEqual(self.client.put(self.report_url, {}).status_code, 405)

    def test_teacher_cannot_submit_report_for_unassigned_course_session(self) -> None:
        unassigned_course = Course.objects.create(
            semester=self.semester,
            name="Network Security",
            level=Course.LevelChoices.ADVANCED,
            start_date=timezone.now().date() - timedelta(days=20),
            end_date=timezone.now().date() + timedelta(days=20),
            sessions_length=Course.SessionLengthChoices.MIN90,
            created_by=self.admin,
            updated_by=self.admin,
        )
        session = self._create_session(
            course=unassigned_course,
            hours_before_end=20,
        )

        response = self._submit_report(
            self.teacher,
            session,
            self._create_report_payload(
                session.id,
                summary="Not assigned to this class.",
            ),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Report.objects.filter(session=session).exists())

    def test_teacher_cannot_submit_duplicate_report_for_same_session(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )

        response = self._submit_report(self.teacher, session)
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(Report.objects.filter(session=session).count(), 1)
        try:
            duplicate_response = self._submit_report(
                self.teacher,
                session,
                self._create_report_payload(session.id, attendees=5),
            )
        except IntegrityError:
            return

        self.assertNotEqual(
            duplicate_response.status_code, 201, duplicate_response.data
        )
        self.assertEqual(Report.objects.filter(session=session).count(), 1)

    def test_teacher_sees_only_own_reports(self) -> None:
        own_session = self._create_session(course=self.course, hours_before_end=20)
        other_session = self._create_session(
            course=self.other_course, hours_before_end=20
        )
        own_report = Report.objects.create(
            session=own_session,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Own report",
            number_of_attendees=11,
            number_of_absentees=1,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ReportHistory.objects.create(
            report=own_report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )
        other_report = Report.objects.create(
            session=other_session,
            teacher_profile=self.teacher_profile2,
            tutorial_summary="Other report",
            number_of_attendees=9,
            number_of_absentees=1,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ReportHistory.objects.create(
            report=other_report,
            user=self.teacher2,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )

        self.client.force_authenticate(self.teacher)
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_report.id)

    def test_teacher_cannot_retrieve_another_teachers_report(self) -> None:
        other_session = self._create_session(
            course=self.other_course, hours_before_end=20
        )
        other_report = Report.objects.create(
            session=other_session,
            teacher_profile=self.teacher_profile2,
            tutorial_summary="Other report",
            number_of_attendees=12,
            number_of_absentees=0,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ReportHistory.objects.create(
            report=other_report,
            user=self.teacher2,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )

        self.client.force_authenticate(self.teacher)
        response = self.client.get(
            reverse("education:report-detail", kwargs={"pk": other_report.id})
        )
        self.assertEqual(response.status_code, 404, response.data)
