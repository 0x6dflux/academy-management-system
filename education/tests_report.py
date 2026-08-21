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
