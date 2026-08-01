from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from account.models import TeacherProfile
from education.models import (
    AcademicClass,
    Report,
    School,
    SchoolContactPerson,
    Session,
    TeacherAcademicClass,
)

if TYPE_CHECKING:
    from account.models import User


USER: User = get_user_model()  # type: ignore


class SystemTestCase(TestCase):
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
        # Teacher
        self.teacher = USER.objects.create_user(
            username="mhd_TCH",
            password="3-tch",
            role="TCH",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Teacher Profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Mahdi",
            last_name="Mohammadi",
            phone_number="1",
            emergency_phone_number="2",
            created_by=self.teacher,
            updated_by=self.teacher,
        )
        # Teacher without profile
        self.on_fly_teacher = USER.objects.create_user(
            "on-the-fly-user",
            "",
            "123",
            role="TCH",
        )
        # School
        self.school = School.objects.create(
            name="Pandi",
            serial_number="SC0001",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # School Contact Person
        self.school_CP1 = SchoolContactPerson.objects.create(
            school=self.school,
            first_name="Ali",
            last_name="Alizadeh",
            phone_number="1",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.school_CP2 = SchoolContactPerson.objects.create(
            school=self.school,
            first_name="Majid",
            last_name="Dehghan",
            phone_number="2",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Academic Class
        self.academic_class = AcademicClass.objects.create(
            name="Math",
            level=AcademicClass.LevelChoices.BASIC,
            start_date=now(),
            end_date=now() + timedelta(days=30),
            serial_number="AC0001",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Session
        self.session = Session.objects.create(
            academic_class=self.academic_class,
            name="Summation",
            duration=Session.DurationChoices.MIN60,
            date=now().date(),
            start_time=now().time(),
            end_time=(now() + timedelta(hours=1)).time(),
            serial_number="SS0001",
            tutorial_summary="The concept of summation has been taught will lots of examples.",
            number_of_attendees=15,
            number_of_absentees=2,
        )
        # Teacher_AcademicClass through table
        self.tac = TeacherAcademicClass.objects.create(
            teacher_profile=self.teacher_profile,
            academic_class=self.academic_class,
            started_at=now(),
            ended_at=now() + timedelta(hours=1),
        )
        # Report
        self.report = Report.objects.create(
            teacher_academic_class=self.tac,
            session=self.session,
            name="Summation Session Report",
            description="The concept of summation has been taught will lots of examples.",
            submission_date=now(),
            is_delayed=False,
            serial_number="RP0001",
        )

    def test_managers(self):
        self.assertEqual(
            TeacherProfile.all_objects.count(),
            TeacherProfile.objects.count(),
            "Inconsistent users in `all_objects` and `objects` managers before soft deletion!",
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher),
            TeacherProfile.objects.get(user=self.teacher),
            f"Inconsistent teacher profile for {self.teacher} user!",
        )

        # not a good test!?
        # self.assertEqual(
        #     TeacherProfile.all_objects.all(),
        #     TeacherProfile.objects.all(),
        #     "Inconsistent teacher profiles!",
        # )

        TeacherProfile.objects.get(user=self.teacher).soft_delete(updated_by=self.admin)

        self.assertRaises(
            TeacherProfile.DoesNotExist,
            TeacherProfile.objects.get,
            user=self.teacher,
        )

    def test_soft_delete(self):
        TeacherProfile.objects.get(user=self.teacher).soft_delete(updated_by=self.admin)

        self.assertEqual(
            TeacherProfile.all_objects.count() - 1,
            TeacherProfile.objects.count(),
            "Inconsistent users in `all_objects` and `objects` managers after soft deletion!",
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher).is_deleted,
            True,
            f"{self.teacher_profile} profile not soft deleted!",
        )

    def test_cascade_soft_delete(self):
        number_of_users_before_soft_delete = USER.all_objects.count()

        # the related field does not exists
        self.on_fly_teacher.soft_delete(updated_by=self.admin)
        number_of_users_after_soft_delete = number_of_users_before_soft_delete - 1
        self.assertEqual(
            number_of_users_after_soft_delete,
            USER.objects.count(),
            "The teacher without profile not soft deleted!",
        )
        self.assertEqual(
            USER.all_objects.get(id=self.on_fly_teacher.pk).is_deleted,
            True,
            "The teacher without profile not soft deleted!",
        )

        # OnToOne relation
        USER.objects.get(id=self.teacher.pk).soft_delete(updated_by=self.admin)
        number_of_users_after_soft_delete -= 1

        # checking the number of objects
        self.assertEqual(
            number_of_users_after_soft_delete,
            USER.objects.count(),
            "Inconsistent users in `all_objects` and `objects` managers after soft deletion!",
        )
        self.assertEqual(
            TeacherProfile.all_objects.count() - 1,
            TeacherProfile.objects.count(),
            "Inconsistent teacher profiles in `all_objects` and `objects` managers after soft deletion!",
        )

        # checking the `is_deleted` field
        self.assertEqual(
            USER.all_objects.get(id=self.teacher.pk).is_deleted,
            True,
            f"{self.teacher} not soft deleted!",
        )
        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher).is_deleted,
            True,
            f"{self.teacher} profile not soft deleted!",
        )

        # OneToMany relation
        School.objects.get(id=self.school.pk).soft_delete(updated_by=self.admin)

        # checking the number of objects
        self.assertEqual(
            School.all_objects.count() - 1,
            School.objects.count(),
            "Inconsistent schools in `all_objects` and `objects` managers after soft deletion!",
        )
        self.assertEqual(
            SchoolContactPerson.all_objects.count() - 2,
            SchoolContactPerson.objects.count(),
            "Inconsistent teacher profiles in `all_objects` and `objects` managers after soft deletion!",
        )

        # checking the `is_deleted` field
        self.assertEqual(
            School.all_objects.get(id=self.school.pk).is_deleted,
            True,
            f"{self.school} not soft deleted!",
        )
        self.assertEqual(
            SchoolContactPerson.all_objects.get(id=self.school_CP1.pk).is_deleted,
            True,
            f"{self.school_CP1} not soft deleted!",
        )
        self.assertEqual(
            SchoolContactPerson.all_objects.get(id=self.school_CP2.pk).is_deleted,
            True,
            f"{self.school_CP2} not soft deleted!",
        )

        # todo: recursive relation
        AcademicClass.objects.get(id=self.academic_class.pk).soft_delete(
            updated_by=self.admin
        )

        # checking the number of objects
        self.assertEqual(
            AcademicClass.all_objects.count() - 1,
            AcademicClass.objects.count(),
            "Inconsistent academic classes after soft deletion!",
        )
        self.assertEqual(
            Session.all_objects.count() - 1,
            Session.objects.count(),
            "Inconsistent sessions after soft deletion!",
        )
        self.assertEqual(
            TeacherAcademicClass.all_objects.count() - 1,
            TeacherAcademicClass.objects.count(),
            "Inconsistent teacher_academic_classes after soft deletion!",
        )
        self.assertEqual(
            Report.all_objects.count() - 1,
            Report.objects.count(),
            "Inconsistent teacher_academic_classes after soft deletion!",
        )
        # checking the `is_deleted` field
        self.assertEqual(
            AcademicClass.all_objects.get(id=self.academic_class.pk).is_deleted,
            True,
            f"{self.academic_class} not soft deleted!",
        )
        self.assertEqual(
            Session.all_objects.get(id=self.session.pk).is_deleted,
            True,
            f"{self.session} not soft deleted!",
        )
        self.assertEqual(
            TeacherAcademicClass.all_objects.get(id=self.tac.pk).is_deleted,
            True,
            f"{self.tac} not soft deleted!",
        )
        self.assertEqual(
            Report.all_objects.get(id=self.report.pk).is_deleted,
            True,
            f"{self.report} not soft deleted!",
        )
