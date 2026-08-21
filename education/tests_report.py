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

    def test_education_officer_queue_contains_only_pending_reports(self) -> None:
        pending = self._create_session(course=self.course, hours_before_end=20)
        rejected = self._create_session(course=self.course, hours_before_end=21)
        approved = self._create_session(course=self.course, hours_before_end=22)
        updated = self._create_session(course=self.course, hours_before_end=23)

        pending_report = self._submit_report(self.teacher, pending)
        rejected_report = self._submit_report(self.teacher, rejected)
        approved_report = self._submit_report(self.teacher, approved)
        updated_report = self._submit_report(self.teacher, updated)

        pending_report = Report.objects.get(pk=pending_report.data["id"])
        rejected_report = Report.objects.get(pk=rejected_report.data["id"])
        approved_report = Report.objects.get(pk=approved_report.data["id"])
        updated_report = Report.objects.get(pk=updated_report.data["id"])

        self._review_report(
            self.education_officer,
            rejected_report,
            is_approved=False,
            description="Needs details",
        )
        self._review_report(
            self.education_officer,
            approved_report,
            is_approved=True,
            description="Looks fine",
        )
        self._review_report(
            self.education_officer,
            updated_report,
            is_approved=False,
            description="First",
        )
        self._edit_report(
            self.teacher,
            updated_report.id,
            self._create_report_payload(updated_report.session.id, summary="Updated"),
        )

        self.client.force_authenticate(self.education_officer)
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200, response.data)
        ids = {item["id"] for item in response.data}
        self.assertIn(pending_report.id, ids)
        self.assertIn(updated_report.id, ids)
        self.assertNotIn(rejected_report.id, ids)
        self.assertNotIn(approved_report.id, ids)

    def test_admin_sees_all_reports(self) -> None:
        pending = self._create_session(course=self.course, hours_before_end=20)
        rejected = self._create_session(course=self.other_course, hours_before_end=20)
        approved = self._create_session(course=self.other_course, hours_before_end=20)

        pending_report = Report.objects.create(
            session=pending,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Pending report",
            number_of_attendees=10,
            number_of_absentees=1,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ReportHistory.objects.create(
            report=pending_report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )
        Report.objects.create(
            session=rejected,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Rejected report",
            number_of_attendees=8,
            number_of_absentees=0,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        approved_report = Report.objects.create(
            session=approved,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Approved report",
            number_of_attendees=9,
            number_of_absentees=2,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        rejected_report = Report.objects.get(session=rejected)
        ReportHistory.objects.create(
            report=approved_report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )

        ReportHistory.objects.create(
            report=rejected_report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )

        ReportHistory.objects.create(
            report=rejected_report,
            user=self.education_officer,
            role=USER.RoleChoices.EDUCATION_OFFICER,
            change=ReportHistory.ChangeChoices.REJECTED,
            description="No",
        )
        ReportHistory.objects.create(
            report=approved_report,
            user=self.education_officer,
            role=USER.RoleChoices.EDUCATION_OFFICER,
            change=ReportHistory.ChangeChoices.APPROVED,
            description="Yes",
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200, response.data)
        ids = {item["id"] for item in response.data}
        self.assertIn(pending_report.id, ids)
        self.assertIn(rejected_report.id, ids)
        self.assertIn(approved_report.id, ids)

    def test_education_officer_cannot_retrieve_finalized_report(self) -> None:
        approved_session = self._create_session(course=self.course, hours_before_end=20)
        rejected_session = self._create_session(course=self.course, hours_before_end=20)

        approved_report = self._submit_report(self.teacher, approved_session)
        rejected_report = self._submit_report(self.teacher, rejected_session)
        approved_report = Report.objects.get(pk=approved_report.data["id"])
        rejected_report = Report.objects.get(pk=rejected_report.data["id"])

        self._review_report(
            self.education_officer,
            approved_report,
            is_approved=True,
            description="Approved",
        )
        self._review_report(
            self.education_officer,
            rejected_report,
            is_approved=False,
            description="Rejected",
        )

        approved_response = self.client.get(
            reverse(
                "education:report-detail",
                kwargs={"pk": approved_report.id},
            )
        )
        rejected_response = self.client.get(
            reverse(
                "education:report-detail",
                kwargs={"pk": rejected_report.id},
            )
        )
        self.assertEqual(approved_response.status_code, 404)
        self.assertEqual(rejected_response.status_code, 404)

    def test_teacher_cannot_edit_pending_or_approved_report(self) -> None:
        pending = self._create_session(course=self.course, hours_before_end=20)
        approved = self._create_session(course=self.course, hours_before_end=20)
        rejected = self._create_session(course=self.course, hours_before_end=20)

        pending_report = Report.objects.create(
            session=pending,
            teacher_profile=self.teacher_profile,
            tutorial_summary="Pending",
            number_of_attendees=10,
            number_of_absentees=1,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ReportHistory.objects.create(
            report=pending_report,
            user=self.teacher,
            role=USER.RoleChoices.TEACHER,
            change=ReportHistory.ChangeChoices.CREATED,
        )

        approved_report_response = self._submit_report(self.teacher, approved)
        rejected_report = self._submit_report(self.teacher, rejected)

        approved_report = Report.objects.get(pk=approved_report_response.data["id"])
        rejected_report = Report.objects.get(pk=rejected_report.data["id"])

        self._review_report(
            self.education_officer,
            approved_report,
            is_approved=True,
            description="Approved",
        )
        self._review_report(
            self.education_officer,
            rejected_report,
            is_approved=False,
            description="Need fix",
        )

        response_pending = self._edit_report(
            self.teacher,
            pending_report.id,
            self._create_report_payload(pending_report.session.id, summary="Nope"),
        )
        response_approved = self._edit_report(
            self.teacher,
            approved_report.id,
            self._create_report_payload(approved_report.session.id, summary="Nope"),
        )
        response_rejected = self._edit_report(
            self.teacher,
            rejected_report.id,
            self._create_report_payload(rejected_report.session.id, summary="Allowed"),
        )

        self.assertEqual(response_pending.status_code, 400, response_pending.data)
        self.assertEqual(response_approved.status_code, 400, response_approved.data)
        self.assertEqual(response_rejected.status_code, 200, response_rejected.data)

        rejected_report.refresh_from_db()
        self.assertEqual(rejected_report.tutorial_summary, "Allowed")

    def test_teacher_can_submit_report_for_own_session(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )

        response = self._submit_report(
            self.teacher,
            session,
            self._create_report_payload(session.id),
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Report.objects.count(), 1)

        report = Report.objects.get(session=session)
        self.assertEqual(report.teacher_profile.user, self.teacher)
        self.assertEqual(report.tutorial_summary, "A short lesson about conditionals.")
        self.assertEqual(report.number_of_attendees, 10)
        self.assertEqual(report.number_of_absentees, 2)

        report_histories = ReportHistory.objects.filter(report=report)
        self.assertEqual(report_histories.count(), 1)
        self.assertEqual(
            report_histories.first().change,
            ReportHistory.ChangeChoices.CREATED,
        )
        self.assertEqual(report_histories.first().user, self.teacher)
        self.assertEqual(report_histories.first().role, USER.RoleChoices.TEACHER)

    def test_teacher_cannot_submit_report_for_unowned_session(self) -> None:
        unowned_session = self._create_session(
            course=self.other_course,
            hours_before_end=20,
        )

        response = self._submit_report(
            self.teacher,
            unowned_session,
            self._create_report_payload(unowned_session.id),
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn(
            "You can only submit reports for sessions assigned to you.",
            str(response.data),
        )
        self.assertEqual(Report.objects.count(), 0)

    def test_report_submission_requires_all_required_fields(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(self.report_url, {"session_id": session.id})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("tutorial_summary", response.data)
        self.assertIn("number_of_attendees", response.data)
        self.assertIn("number_of_absentees", response.data)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_submission_rejects_negative_attendees(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )

        response = self._submit_report(
            self.teacher,
            session,
            self._create_report_payload(session.id, attendees=-1),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("number_of_attendees", response.data)

    def test_report_submission_rejects_negative_absentees(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )

        response = self._submit_report(
            self.teacher,
            session,
            self._create_report_payload(session.id, absentees=-1),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("number_of_absentees", response.data)

    def test_report_submission_rejects_non_integer_attendees(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )

        payload = self._create_report_payload(session.id)
        payload["number_of_attendees"] = "ten"

        response = self._submit_report(self.teacher, session, payload)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("number_of_attendees", response.data)

    def test_report_delay_calculation_exact_cutoff_is_not_late(self) -> None:
        current_local = (
            timezone.now()
            .astimezone(self.local_tz)
            .replace(
                second=0,
                microsecond=0,
            )
        )
        cutoff_session_end = current_local - timedelta(hours=48)
        pseudo_session = Session(
            date=cutoff_session_end.date(),
            start_time=time(9, 0),
            end_time=time(
                cutoff_session_end.hour,
                cutoff_session_end.minute,
                cutoff_session_end.second,
            ),
        )

        with patch(
            "education.serializers.report_serializers.datetime"
        ) as datetime_mock:
            datetime_mock.combine.side_effect = lambda date_obj, time_obj: (
                datetime.combine(date_obj, time_obj)
            )
            datetime_mock.now.return_value = current_local
            is_late, delay_time = (
                ReportSubmissionWriteOnlyModelSerializer.delay_calculation(
                    pseudo_session
                )
            )

        self.assertFalse(is_late)
        self.assertEqual(delay_time, 0)

    def test_report_submission_marks_not_late_within_48_hours(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=47,
        )

        response = self._submit_report(self.teacher, session)
        self.assertEqual(response.status_code, 201, response.data)

        report = Report.objects.get(session=session)
        expected_late, expected_delay = (
            ReportSubmissionWriteOnlyModelSerializer.delay_calculation(session)
        )
        self.assertEqual(report.is_delayed, expected_late)
        self.assertEqual(report.delay_time, expected_delay)

    def test_report_submission_marks_late_after_48_hours(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=50,
        )

        response = self._submit_report(self.teacher, session)
        self.assertEqual(response.status_code, 201, response.data)

        report = Report.objects.get(session=session)
        expected_late, expected_delay = (
            ReportSubmissionWriteOnlyModelSerializer.delay_calculation(session)
        )
        self.assertTrue(expected_late)
        self.assertTrue(report.is_delayed)
        self.assertEqual(report.delay_time, expected_delay)
        self.assertGreaterEqual(report.delay_time, 1)

    def test_edo_list_and_filters_pending_reports(self) -> None:
        today = timezone.now().date()
        in_range_session = self._create_session(
            course=self.course,
            date=today - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 30),
        )
        out_of_range_session = self._create_session(
            course=self.course,
            date=today - timedelta(days=40),
            start_time=time(10, 0),
            end_time=time(11, 30),
        )
        other_school_session = self._create_session(
            course=self.other_course,
            date=today - timedelta(days=2),
            start_time=time(10, 0),
            end_time=time(11, 30),
        )
        self._submit_report(self.teacher, in_range_session)
        self._submit_report(self.teacher, out_of_range_session)
        self._submit_report(self.teacher2, other_school_session)

        self.client.force_authenticate(user=self.education_officer)
        list_response = self.client.get(self.report_url)
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 3)

        school_filtered = self.client.get(self.report_url, {"school": self.school.name})
        self.assertEqual(school_filtered.status_code, 200, school_filtered.data)
        self.assertEqual(len(school_filtered.data), 2)
        school_report_ids = {item["id"] for item in school_filtered.data}
        school_expected_ids = {
            Report.objects.get(session=in_range_session).id,
            Report.objects.get(session=out_of_range_session).id,
        }
        self.assertEqual(school_report_ids, school_expected_ids)

        course_filtered = self.client.get(
            self.report_url, {"course": self.other_course.name}
        )
        self.assertEqual(course_filtered.status_code, 200, course_filtered.data)
        self.assertEqual(len(course_filtered.data), 1)
        self.assertEqual(
            course_filtered.data[0]["id"],
            Report.objects.get(session=other_school_session).id,
        )

        teacher_filtered = self.client.get(
            self.report_url, {"teacher_first_name": self.teacher_profile2.first_name}
        )
        self.assertEqual(teacher_filtered.status_code, 200, teacher_filtered.data)
        self.assertEqual(len(teacher_filtered.data), 1)
        self.assertEqual(
            teacher_filtered.data[0]["id"],
            Report.objects.get(session=other_school_session).id,
        )

        date_range_filtered = self.client.get(
            self.report_url,
            {
                "date_after": str(today - timedelta(days=10)),
                "date_before": str(today),
            },
        )
        self.assertEqual(date_range_filtered.status_code, 200, date_range_filtered.data)
        self.assertEqual(len(date_range_filtered.data), 2)
        self.assertEqual(
            {item["id"] for item in date_range_filtered.data},
            {
                Report.objects.get(session=in_range_session).id,
                Report.objects.get(session=other_school_session).id,
            },
        )

    def test_edo_filters_are_combinable(self) -> None:
        today = timezone.now().date()

        extra_course = Course.objects.create(
            semester=self.semester,
            name="Django Advanced",
            level=Course.LevelChoices.INTERMEDIATE,
            start_date=today - timedelta(days=40),
            end_date=today + timedelta(days=40),
            sessions_length=Course.SessionLengthChoices.MIN120,
            created_by=self.admin,
            updated_by=self.admin,
        )
        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=extra_course,
            started_at=today - timedelta(days=30),
            ended_at=today + timedelta(days=30),
            created_by=self.admin,
            updated_by=self.admin,
        )

        matching_session = self._create_session(
            course=self.course,
            date=today - timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        same_school_wrong_course_session = self._create_session(
            course=extra_course,
            date=today - timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        out_of_range_session = self._create_session(
            course=self.course,
            date=today - timedelta(days=20),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        self._submit_report(self.teacher, matching_session)
        self._submit_report(self.teacher, same_school_wrong_course_session)
        self._submit_report(self.teacher, out_of_range_session)

        self.client.force_authenticate(user=self.education_officer)
        filtered_response = self.client.get(
            self.report_url,
            {
                "school": self.school.name,
                "course": self.course.name,
                "date_after": str(today - timedelta(days=5)),
                "date_before": str(today),
            },
        )
        self.assertEqual(filtered_response.status_code, 200, filtered_response.data)
        self.assertEqual(len(filtered_response.data), 1)
        self.assertEqual(
            filtered_response.data[0]["id"],
            Report.objects.get(session=matching_session).id,
        )

    def test_admin_can_approve_report(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.report_url,
            {
                "report": report.id,
                "is_approved": True,
                "description": "Approved by admin.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)

        report.refresh_from_db()
        self.assertEqual(
            report.histories.order_by("-id").first().change,  # type: ignore[union-attr]
            ReportHistory.ChangeChoices.APPROVED,
        )
        self.assertEqual(
            report.histories.order_by("-id").first().user,  # type: ignore[union-attr]
            self.admin,
        )

    def test_edo_can_review_report_and_requires_rejection_reason(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)

        missing_reason_response = self._review_report(
            self.education_officer,
            report,
            is_approved=False,
            description="   ",
        )
        self.assertEqual(
            missing_reason_response.status_code,
            400,
            missing_reason_response.data,
        )
        self.assertIn(
            "Description shall not be blank if the report is not approved.",
            str(missing_reason_response.data),
        )

        review_response = self._review_report(
            self.education_officer,
            report,
            is_approved=True,
            description="Looks good",
        )
        self.assertEqual(review_response.status_code, 201, review_response.data)

        report.refresh_from_db()
        self.assertEqual(
            report.histories.order_by("-id").first().change,
            ReportHistory.ChangeChoices.APPROVED,
        )
        self.assertEqual(
            report.histories.order_by("-id").first().user, self.education_officer
        )

        self.client.force_authenticate(user=self.education_officer)
        pending_list = self.client.get(self.report_url)
        self.assertEqual(pending_list.status_code, 200, pending_list.data)
        self.assertEqual(pending_list.data, [])

    def test_edo_cannot_review_already_finalized_report(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)

        self._review_report(
            self.education_officer,
            report,
            is_approved=True,
            description="Approved first time.",
        )

        second_review = self._review_report(
            self.education_officer,
            report,
            is_approved=False,
            description="Second review should fail.",
        )
        self.assertEqual(second_review.status_code, 400, second_review.data)
        self.assertIn("already finalized", str(second_review.data))

    def test_bulk_approval_rejects_empty_report_list(self) -> None:
        self.client.force_authenticate(user=self.education_officer)
        response = self.client.post(
            self.bulk_approval_url,
            {"reports": []},
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("may not be empty", str(response.data))

    def test_report_history_patch_rejects_missing_fields(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        history = ReportHistory.objects.latest("id")
        history_url = reverse(
            "education:report-history-detail", kwargs={"pk": history.id}
        )

        self.client.force_authenticate(user=self.education_officer)
        no_is_approved = self.client.patch(
            history_url, {"description": "Only description"}
        )
        self.assertEqual(no_is_approved.status_code, 400, no_is_approved.data)
        self.assertIn("is_approved", str(no_is_approved.data))

        no_description = self.client.patch(
            history_url,
            {"is_approved": False},
        )
        self.assertEqual(no_description.status_code, 400, no_description.data)
        self.assertIn("description", str(no_description.data))

        no_missing_description = self.client.patch(
            history_url,
            {"is_approved": False, "description": "   "},
        )
        self.assertEqual(
            no_missing_description.status_code, 400, no_missing_description.data
        )
        self.assertIn(
            "Description shall not be blank", str(no_missing_description.data)
        )

    def test_report_history_patch_can_append_review_entry(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)
        initial_count = ReportHistory.objects.filter(report=report).count()

        history = ReportHistory.objects.latest("id")
        history_url = reverse(
            "education:report-history-detail", kwargs={"pk": history.id}
        )

        self.client.force_authenticate(user=self.education_officer)
        patch_response = self.client.patch(
            history_url,
            {"is_approved": False, "description": "Reviewer found missing details."},
        )
        self.assertEqual(patch_response.status_code, 200, patch_response.data)

        report.refresh_from_db()
        self.assertEqual(
            report.histories.count(),
            initial_count + 1,
        )
        latest_history = report.histories.order_by("-id").first()
        self.assertEqual(latest_history.change, ReportHistory.ChangeChoices.REJECTED)
        self.assertEqual(latest_history.user, self.education_officer)
        self.assertEqual(latest_history.description, "Reviewer found missing details.")

    def test_education_officer_cannot_update_report_content(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)
        old_summary = report.tutorial_summary

        self.client.force_authenticate(user=self.education_officer)
        response = self.client.put(
            reverse("education:report-detail", kwargs={"pk": report.id}),
            {"report": report.id, "is_approved": True, "tutorial_summary": "Hacked"},
        )
        self.assertEqual(response.status_code, 400, response.data)

        report.refresh_from_db()
        self.assertEqual(report.tutorial_summary, old_summary)

    def test_report_history_permissions(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        history = ReportHistory.objects.latest("id")

        response = self.client.get(self.report_history_url)
        self.assertEqual(response.status_code, 403, response.data)

        self.client.force_authenticate(user=self.finance_officer)
        self.assertEqual(self.client.get(self.report_history_url).status_code, 403)

        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(self.client.get(self.report_history_url).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse(
                    "education:report-history-detail",
                    kwargs={"pk": history.id},
                )
            ).status_code,
            403,
        )

        self.client.force_authenticate(user=self.education_officer)
        self.assertEqual(self.client.get(self.report_history_url).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse(
                    "education:report-history-detail",
                    kwargs={"pk": history.id},
                )
            ).status_code,
            200,
        )

        self.client.force_authenticate(user=self.teacher)
        patch_response = self.client.patch(
            reverse(
                "education:report-history-detail",
                kwargs={"pk": history.id},
            ),
            {"is_approved": True, "description": "No"},
        )
        self.assertEqual(patch_response.status_code, 403, patch_response.data)

        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(self.report_history_url).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse(
                    "education:report-history-detail",
                    kwargs={"pk": history.id},
                )
            ).status_code,
            200,
        )

    def test_report_history_rejects_unsupported_methods(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        history = ReportHistory.objects.latest("id")
        history_detail_url = reverse(
            "education:report-history-detail",
            kwargs={"pk": history.id},
        )

        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.post(self.report_history_url, {}).status_code, 405)
        self.assertEqual(self.client.put(self.report_history_url, {}).status_code, 405)
        self.assertEqual(self.client.delete(self.report_history_url).status_code, 405)
        self.assertEqual(self.client.delete(history_detail_url).status_code, 405)
        self.assertEqual(self.client.put(history_detail_url, {}).status_code, 405)

    def test_report_bulk_approval_permissions(self) -> None:
        session = self._create_session(course=self.course, hours_before_end=20)
        report = self._submit_report(self.teacher, session)
        report_id = report.data["id"]

        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(
            self.client.post(
                self.bulk_approval_url,
                {"reports": [report_id]},
            ).status_code,
            403,
        )

        self.client.force_authenticate(user=self.finance_officer)
        self.assertEqual(
            self.client.post(
                self.bulk_approval_url,
                {"reports": [report_id]},
            ).status_code,
            403,
        )

        self.client.force_authenticate(user=self.education_officer)
        self.assertEqual(
            self.client.post(
                self.bulk_approval_url,
                {"reports": [report_id]},
            ).status_code,
            201,
        )

    def test_report_bulk_approval_rejects_unsupported_methods(self) -> None:
        session = self._create_session(course=self.course, hours_before_end=20)
        report = self._submit_report(self.teacher, session)
        report_id = report.data["id"]

        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(self.bulk_approval_url).status_code, 405)
        self.assertEqual(self.client.delete(self.bulk_approval_url).status_code, 405)
        self.assertEqual(
            self.client.post(
                self.bulk_approval_url,
                {"reports": [report_id]},
            ).status_code,
            201,
        )

    def test_teacher_report_stat_permissions(self) -> None:
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(
            self.client.get(self.teacher_report_stat_url, {"days": 30}).status_code,
            200,
        )

        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(
            self.client.get(self.teacher_report_stat_url, {"days": 30}).status_code,
            200,
        )

        self.client.force_authenticate(user=self.finance_officer)
        self.assertEqual(
            self.client.get(self.teacher_report_stat_url, {"days": 30}).status_code,
            403,
        )

        self.client.force_authenticate(user=self.education_officer)
        self.assertEqual(
            self.client.get(self.teacher_report_stat_url, {"days": 30}).status_code,
            403,
        )

        self.client.logout()
        self.assertEqual(
            self.client.get(self.teacher_report_stat_url, {"days": 30}).status_code,
            401,
        )

    def test_teacher_cannot_approve_their_own_report(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)
        history_count_before = ReportHistory.objects.filter(report=report).count()

        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            self.report_url,
            {
                "report": report.id,
                "is_approved": True,
                "description": "Attempted approval",
            },
        )
        self.assertNotEqual(response.status_code, 201, response.data)
        self.assertEqual(
            ReportHistory.objects.filter(report=report).count(),
            history_count_before,
        )

    def test_teacher_can_edit_rejected_report_and_resubmit(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, session)
        report = Report.objects.get(session=session)

        reject_response = self._review_report(
            self.education_officer,
            report,
            is_approved=False,
            description="Missing detail",
        )
        self.assertEqual(reject_response.status_code, 201, reject_response.data)
        self.assertEqual(
            self._latest_history_change(report), ReportHistory.ChangeChoices.REJECTED
        )

        update_response = self._edit_report(
            self.teacher,
            report.id,
            self._create_report_payload(
                session.id,
                summary="Updated report content",
                attendees=15,
                absentees=1,
            ),
        )
        self.assertNotEqual(
            update_response.status_code,
            405,
            update_response.data,
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        report.refresh_from_db()
        self.assertEqual(report.tutorial_summary, "Updated report content")
        self.assertEqual(report.number_of_attendees, 15)
        self.assertEqual(report.number_of_absentees, 1)
        self.assertEqual(
            self._latest_history_change(report), ReportHistory.ChangeChoices.UPDATED
        )

        resubmit_response = self._review_report(
            self.education_officer,
            report,
            is_approved=True,
            description="Updated and approved",
        )
        self.assertEqual(resubmit_response.status_code, 201, resubmit_response.data)
        self.assertEqual(
            self._latest_history_change(report), ReportHistory.ChangeChoices.APPROVED
        )

        history_changes = list(
            ReportHistory.objects.filter(report=report)
            .order_by("id")
            .values_list("change", flat=True)
        )
        self.assertIn(ReportHistory.ChangeChoices.CREATED, history_changes)
        self.assertIn(ReportHistory.ChangeChoices.REJECTED, history_changes)
        self.assertIn(ReportHistory.ChangeChoices.UPDATED, history_changes)
        self.assertIn(ReportHistory.ChangeChoices.APPROVED, history_changes)

    def test_late_rule_recalculates_on_rejected_report_edit(self) -> None:
        session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        response = self._submit_report(self.teacher, session)
        self.assertEqual(response.status_code, 201, response.data)
        report = Report.objects.get(session=session)
        self.assertFalse(report.is_delayed)
        self.assertEqual(report.delay_time, 0)

        self._review_report(
            self.education_officer,
            report,
            is_approved=False,
            description="Need more detail",
        )

        old_session_datetime = timezone.now().astimezone(self.local_tz) - timedelta(
            hours=50
        )
        session.date = old_session_datetime.date()
        session.end_time = time(
            old_session_datetime.hour,
            old_session_datetime.minute,
            second=0,
            microsecond=0,
        )
        session.save(update_fields=("date", "end_time"))

        update_response = self._edit_report(
            self.teacher,
            report.id,
            self._create_report_payload(session.id, summary="Updated after reject"),
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        report.refresh_from_db()
        self.assertTrue(report.is_delayed)
        self.assertGreater(report.delay_time, 0)

    def test_report_status_properties_follow_latest_history(self) -> None:
        create_session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, create_session)
        created_report = Report.objects.get(session=create_session)

        self.assertFalse(created_report.is_approved)
        self.assertFalse(created_report.can_TCH_update)
        self.assertIsNone(created_report.rej_desc)

        self._review_report(
            self.education_officer,
            created_report,
            is_approved=False,
            description="Missing materials",
        )
        created_report.refresh_from_db()
        self.assertFalse(created_report.is_approved)
        self.assertTrue(created_report.can_TCH_update)
        self.assertEqual(created_report.rej_desc, "Missing materials")

        approved_session = self._create_session(
            course=self.course,
            hours_before_end=20,
        )
        self._submit_report(self.teacher, approved_session)
        approved_report = Report.objects.get(session=approved_session)
        self._review_report(
            self.education_officer,
            approved_report,
            is_approved=True,
            description="Looks good",
        )
        approved_report.refresh_from_db()
        self.assertTrue(approved_report.is_approved)
        self.assertFalse(approved_report.can_TCH_update)


class ReportLifecycleOptionalTestCase(TestCase, EndpointTestsMixin):
    def setUp(self) -> None:
        # ==================
        # setup the database
        # ==================
        self.admin = USER.objects.create_user(
            "ADM2@example.com",
            "0@dmin",
            role=USER.RoleChoices.ADMIN,
        )
        self.education_officer = USER.objects.create_user(
            "EDO2@example.com",
            "1/edo",
            role=USER.RoleChoices.EDUCATION_OFFICER,
        )
        self.teacher = USER.objects.create_user(
            "TCH3@example.com",
            "2-tch",
            role=USER.RoleChoices.TEACHER,
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Neda",
            last_name="Rahimi",
            mobile_number="091200000003",
            landline_number="02130000003",
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.school = School.objects.create(
            name="Shahr",
            email="shahr@school.com",
            landline_number="0219999999",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.semester = Semester.objects.create(
            school=self.school,
            name="Fall 2",
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=30),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.course = Course.objects.create(
            semester=self.semester,
            name="Machine Learning",
            level=Course.LevelChoices.INTERMEDIATE,
            start_date=timezone.now().date() - timedelta(days=20),
            end_date=timezone.now().date() + timedelta(days=20),
            sessions_length=Course.SessionLengthChoices.MIN60,
            created_by=self.admin,
            updated_by=self.admin,
        )
        TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=self.course,
            started_at=timezone.now().date() - timedelta(days=18),
            ended_at=timezone.now().date() + timedelta(days=18),
            created_by=self.admin,
            updated_by=self.admin,
        )

        self.client = APIClient()
        self.local_tz = pytz.timezone(TIME_ZONE)
        self.report_url = reverse("education:report-list")
        self.bulk_approval_url = reverse("education:report-bulk-approval")
        self.teacher_report_stat_url = reverse("education:teacher-report-stat")

    def _create_session(self, *, course: Course, date_shift: int) -> Session:
        session_date = timezone.now().date() - timedelta(days=date_shift)
        return Session.objects.create(
            course=course,
            date=session_date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            created_by=self.admin,
            updated_by=self.admin,
        )

    def _submit_report(self, user: USER, session: Session, *, summary: str) -> Report:
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.report_url,
            {
                "session_id": session.id,
                "tutorial_summary": summary,
                "number_of_attendees": 7,
                "number_of_absentees": 1,
            },
        )
        self.assertEqual(response.status_code, 201)
        return Report.objects.get(session=session)

    def _review_report(
        self,
        user: USER,
        report: Report,
        *,
        is_approved: bool,
        description: str,
    ) -> None:
        self.client.force_authenticate(user=user)
        payload = {
            "report": report.id,
            "is_approved": is_approved,
            "description": description,
        }
        response = self.client.post(self.report_url, payload)
        self.assertEqual(response.status_code, 201, response.data)

    def test_teacher_report_stat_summary(self) -> None:
        recent_session = self._create_session(course=self.course, date_shift=2)
        pending_session = self._create_session(course=self.course, date_shift=5)
        rejected_session = self._create_session(course=self.course, date_shift=6)

        pending_report = self._submit_report(
            self.teacher,
            pending_session,
            summary="Pending session",
        )
        rejected_report = self._submit_report(
            self.teacher,
            rejected_session,
            summary="Rejected session",
        )
        approved_report = self._submit_report(
            self.teacher,
            recent_session,
            summary="Approved session",
        )

        self._review_report(
            self.education_officer,
            rejected_report,
            is_approved=False,
            description="Need detail",
        )
        self._review_report(
            self.education_officer,
            approved_report,
            is_approved=True,
            description="Looks good",
        )

        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.teacher_report_stat_url, {"days": 30})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["approved"], 1)
        self.assertEqual(response.data["rejected"], 1)
        self.assertEqual(response.data["pending_review"], 1)
        self.assertEqual(response.data["not_submitted"], 0)

    def test_bulk_approve_multiple_reports(self) -> None:
        session_one = self._create_session(course=self.course, date_shift=1)
        session_two = self._create_session(course=self.course, date_shift=2)
        report_one = self._submit_report(
            self.teacher,
            session_one,
            summary="Session one",
        )
        report_two = self._submit_report(
            self.teacher,
            session_two,
            summary="Session two",
        )

        self.client.force_authenticate(user=self.education_officer)
        response = self.client.post(
            self.bulk_approval_url,
            {"reports": [report_one.id, report_two.id]},
        )

        self.assertEqual(response.status_code, 201, response.data)

        for report in (report_one, report_two):
            self.assertEqual(
                ReportHistory.objects.filter(
                    report=report,
                )
                .order_by("-id")
                .first()
                .change,
                ReportHistory.ChangeChoices.APPROVED,
            )

    def test_bulk_approval_rejects_reviewed_reports(self) -> None:
        session_one = self._create_session(course=self.course, date_shift=3)
        session_two = self._create_session(course=self.course, date_shift=4)
        pending_report = self._submit_report(
            self.teacher,
            session_one,
            summary="Pending review",
        )
        reviewed_report = self._submit_report(
            self.teacher,
            session_two,
            summary="Already approved",
        )
        self._review_report(
            self.education_officer,
            reviewed_report,
            is_approved=True,
            description="Approved",
        )

        self.client.force_authenticate(user=self.education_officer)
        response = self.client.post(
            self.bulk_approval_url,
            {"reports": [pending_report.id, reviewed_report.id]},
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn(str(reviewed_report.id), str(response.data))

        self.assertEqual(
            ReportHistory.objects.filter(
                report=reviewed_report, change=ReportHistory.ChangeChoices.APPROVED
            ).count(),
            1,
        )

    def test_report_history_keeps_audit_information(self) -> None:
        self.client.force_authenticate(user=self.teacher)
        report_session = self._create_session(course=self.course, date_shift=1)
        report = self._submit_report(
            self.teacher,
            report_session,
            summary="History flow",
        )

        histories = ReportHistory.objects.filter(report=report)
        self.assertEqual(histories.count(), 1)
        initial_history = histories.first()
        self.assertIsNotNone(initial_history.user)
        self.assertEqual(initial_history.role, USER.RoleChoices.TEACHER)
        self.assertIsNotNone(initial_history.modified_at)

        self.client.force_authenticate(user=self.education_officer)
        self._review_report(
            self.education_officer,
            report,
            is_approved=False,
            description="Rejected for audit",
        )

        final_history = (
            ReportHistory.objects.filter(report=report).order_by("-id").first()
        )
        self.assertEqual(final_history.change, ReportHistory.ChangeChoices.REJECTED)
        self.assertEqual(final_history.user, self.education_officer)
        self.assertEqual(final_history.role, USER.RoleChoices.EDUCATION_OFFICER)
        self.assertIsNotNone(final_history.modified_at)
        self.assertEqual(final_history.description, "Rejected for audit")

        total_changes = (
            ReportHistory.objects.filter(report=report)
            .order_by("id")
            .values_list("change", flat=True)
        )
        self.assertIn(ReportHistory.ChangeChoices.CREATED, total_changes)
        self.assertIn(ReportHistory.ChangeChoices.REJECTED, total_changes)

    def test_teacher_report_stat_with_no_reports_returns_zero_counts(self) -> None:
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.teacher_report_stat_url, {"days": 30})

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["total_sessions"], 0)
        self.assertEqual(response.data["not_submitted"], 0)
        self.assertEqual(response.data["pending_review"], 0)
        self.assertEqual(response.data["rejected"], 0)
        self.assertEqual(response.data["approved"], 0)
