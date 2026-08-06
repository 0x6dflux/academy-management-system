from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from account.models import TeacherProfile, User
from education.models import (
    Course,
    Report,
    School,
    SchoolContactPerson,
    Semester,
    Session,
    TeacherCourse,
)

USER = User


class SystemTestCase(TestCase):
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
        # Teacher
        self.teacher = USER.objects.create_user(
            "TCH@example.com",
            "3-tch",
            role="TCH",
        )
        # Teacher Profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            first_name="Mahdi",
            last_name="Mohammadi",
            mobile_number="0989361234567",
            landline_number="0982112345678",
            created_by=self.teacher,
            updated_by=self.teacher,
        )
        # Teacher without profile
        self.on_fly_teacher = USER.objects.create_user(
            "on-the-fly-user@example.com",
            "123",
            role="TCH",
        )
        # School
        self.school = School.objects.create(
            name="Pandi",
            email="pandi.com",
            landline_number="0982112345678",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # School Contact Person
        self.school_CP1 = SchoolContactPerson.objects.create(
            school=self.school,
            first_name="Ali",
            last_name="Alizadeh",
            school_role=SchoolContactPerson.SchoolRoleChoices.MANAGER,
            mobile_number="0989191234567",
            landline_extension_number="1234",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.school_CP2 = SchoolContactPerson.objects.create(
            school=self.school,
            first_name="Majid",
            last_name="Dehghan",
            school_role=SchoolContactPerson.SchoolRoleChoices.DEPUTY,
            mobile_number="0989191234567",
            landline_extension_number="1234",
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Semester
        self.semester = Semester.objects.create(
            school=self.school,
            name="spring",
            start_date=now(),
            end_date=now() + timedelta(days=90),
            is_summer_semester=False,
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Course
        self.course = Course.objects.create(
            semester=self.semester,
            name="Math",
            level=Course.LevelChoices.BASIC,
            start_date=now() + timedelta(days=10),
            end_date=now() + timedelta(days=40),
            sessions_length=Course.SessionLengthChoices.MIN60,
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Session
        self.session = Session.objects.create(
            course=self.course,
            date=now(),
            start_time=now(),
            end_time=now() + timedelta(hours=1),
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Teacher_Course through table
        self.teacher_course = TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            course=self.course,
            started_at=now(),
            ended_at=now() + timedelta(days=10),
            created_by=self.admin,
            updated_by=self.admin,
        )
        # Report
        self.report = Report.objects.create(
            session=self.session,
            teacher_profile=self.teacher_profile,
            tutorial_summary="The concept of summation has been taught will lots of examples.",
            number_of_attendees=12,
            number_of_absentees=3,
            is_delayed=False,
            delay_time=0,
            created_by=self.admin,
            updated_by=self.admin,
        )

    def test_managers(self):
        self.assertEqual(
            TeacherProfile.all_objects.count(),
            TeacherProfile.objects.count(),
            "Inconsistent users by managers before soft deletion!",
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher),
            TeacherProfile.objects.get(user=self.teacher),
            f"Inconsistent teacher profile for {self.teacher} user before soft deletion!",
        )

        TeacherProfile.objects.get(user=self.teacher).soft_delete(updated_by=self.admin)

        self.assertRaises(
            TeacherProfile.DoesNotExist,
            TeacherProfile.objects.get,
            user=self.teacher,
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher),
            self.teacher_profile,
            f"Inconsistent teacher profile for {self.teacher} user after soft deletion!",
        )

    def test_obj_soft_delete(self):
        TeacherProfile.objects.get(user=self.teacher).soft_delete(updated_by=self.admin)

        self.assertEqual(
            TeacherProfile.all_objects.count() - 1,
            TeacherProfile.objects.count(),
            "Inconsistent users count after soft deletion!",
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher).is_deleted,
            True,
            f"{self.teacher_profile} profile not soft deleted!",
        )

    def test_queryset_soft_delete(self):
        TeacherProfile.objects.all().soft_delete(updated_by=self.admin)  # type: ignore

        self.assertEqual(
            TeacherProfile.all_objects.count() - 1,
            TeacherProfile.objects.count(),
            "Inconsistent users count after soft deletion!",
        )

        self.assertEqual(
            TeacherProfile.all_objects.get(user=self.teacher).is_deleted,
            True,
            f"{self.teacher_profile} profile not soft deleted!",
        )

    def test_no_relation_field_cascade_soft_delete(self):
        # the related field does not exists
        self.on_fly_teacher.soft_delete(updated_by=self.admin)
        self.assertEqual(
            USER.all_objects.count() - 1,
            USER.objects.count(),
            "The teacher without profile not soft deleted!",
        )
        self.assertEqual(
            USER.all_objects.get(id=self.on_fly_teacher.pk).is_deleted,
            True,
            "The teacher without profile not soft deleted!",
        )

    def test_one_to_one_relation_field_cascade_soft_delete(self):
        # OnToOne relation
        USER.objects.get(id=self.teacher.pk).soft_delete(updated_by=self.admin)

        # checking the number of objects
        self.assertEqual(
            USER.all_objects.count() - 1,
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

    def test_one_to_many_relation_field_cascade_soft_delete(self):
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

    def test_recursive_relation_fields_cascade_soft_delete(self):
        Course.objects.get(id=self.course.pk).soft_delete(updated_by=self.admin)

        # checking the number of objects
        self.assertEqual(
            Course.all_objects.count() - 1,
            Course.objects.count(),
            "Inconsistent academic classes after soft deletion!",
        )
        self.assertEqual(
            Session.all_objects.count() - 1,
            Session.objects.count(),
            "Inconsistent sessions after soft deletion!",
        )
        self.assertEqual(
            TeacherCourse.all_objects.count() - 1,
            TeacherCourse.objects.count(),
            "Inconsistent teacher_academic_classes after soft deletion!",
        )
        self.assertEqual(Report.objects.count(), 1, "Inconsistent number of reports!")

        # checking the `is_deleted` field
        self.assertEqual(
            Course.all_objects.get(id=self.course.pk).is_deleted,
            True,
            f"{self.course} not soft deleted!",
        )
        self.assertEqual(
            Session.all_objects.get(id=self.session.pk).is_deleted,
            True,
            f"{self.session} not soft deleted!",
        )
        self.assertEqual(
            TeacherCourse.all_objects.get(pk=self.teacher_course.pk).is_deleted,
            True,
            f"{self.teacher_course} not soft deleted!",
        )
        with self.assertRaises(AttributeError):
            Report.objects.get(id=self.report.pk).is_deleted  # type: ignore
