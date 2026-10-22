"""Kurs tuzilmasi, seed va guruh qoidalari testlari."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from audit.models import AuditLog

from . import seed_data
from .models import Course, Group, GroupMember, Lesson, Module


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password="Sinov-parol-2026", role=role)


class SeedTests(TestCase):
    """Data migratsiya natijasi."""

    def setUp(self) -> None:
        self.course = Course.objects.get(slug=seed_data.COURSE["slug"])

    def test_course_has_4_modules_and_48_lessons(self) -> None:
        self.assertEqual(self.course.modules.count(), 4)
        self.assertEqual(Lesson.objects.filter(module__course=self.course).count(), 48)

    def test_lessons_numbered_1_to_48_in_order(self) -> None:
        numbers = list(Lesson.objects.filter(module__course=self.course).values_list("number", flat=True))
        self.assertEqual(numbers, list(range(1, 49)))

    def test_each_module_has_12_lessons(self) -> None:
        for module in self.course.modules.all():
            self.assertEqual(module.lessons.count(), 12, module)

    def test_lesson_titles_and_kinds(self) -> None:
        self.assertEqual(Lesson.objects.get(number=9).title, "match-case")
        self.assertEqual(Lesson.objects.get(number=12).kind, Lesson.Kind.PROJECT_DEFENSE)
        self.assertEqual(Lesson.objects.get(number=36).kind, Lesson.Kind.PROJECT_DEFENSE)
        self.assertEqual(Lesson.objects.get(number=48).kind, Lesson.Kind.DEMO_DAY)
        self.assertEqual(Lesson.objects.get(number=10).kind, Lesson.Kind.LESSON)

    def test_sample_group_with_teacher_nurbek(self) -> None:
        group = Group.objects.get(name="Python-1")
        self.assertEqual(group.teacher.username, "nurbek")
        self.assertTrue(group.teacher.is_superadmin)
        self.assertEqual(group.course, self.course)

    def test_seed_is_idempotent(self) -> None:
        import importlib

        from django.apps import apps

        seed_module = importlib.import_module("courses.migrations.0002_seed_course")
        seed_module.seed(apps, None)
        self.assertEqual(Course.objects.filter(slug=seed_data.COURSE["slug"]).count(), 1)
        self.assertEqual(Module.objects.count(), 4)
        self.assertEqual(Lesson.objects.count(), 48)
        self.assertEqual(Group.objects.filter(name="Python-1").count(), 1)


class StructureRuleTests(TestCase):
    """Model qoidalari."""

    def setUp(self) -> None:
        self.course = Course.objects.get(slug=seed_data.COURSE["slug"])
        self.teacher = make_user("ustoz", Role.MODERATOR)
        self.student = make_user("talaba")
        self.g1 = Group.objects.create(course=self.course, name="A", teacher=self.teacher)
        self.g2 = Group.objects.create(course=self.course, name="B", teacher=self.teacher)

    def test_lesson_number_unique_across_course(self) -> None:
        module2 = self.course.modules.get(number=2)
        lesson = Lesson(module=module2, number=5, title="Dublikat")
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_group_teacher_must_be_moderator(self) -> None:
        jury_pro = make_user("pro", Role.JURY_PRO)
        group = Group(course=self.course, name="C", teacher=jury_pro)
        with self.assertRaises(ValidationError):
            group.full_clean()
        Group(course=self.course, name="D", teacher=self.teacher).full_clean()

    def test_one_active_group_per_course(self) -> None:
        GroupMember.objects.create(group=self.g1, user=self.student)
        with self.assertRaises(ValidationError):
            GroupMember.objects.create(group=self.g2, user=self.student)

    def test_inactive_membership_allows_another_group(self) -> None:
        GroupMember.objects.create(group=self.g1, user=self.student, is_active=False)
        GroupMember.objects.create(group=self.g2, user=self.student)
        self.assertEqual(self.student.group_memberships.count(), 2)

    def test_member_can_be_in_groups_of_different_courses(self) -> None:
        other = Course.objects.create(title="Algoritmlar", slug="algo")
        g3 = Group.objects.create(course=other, name="Algo-1", teacher=self.teacher)
        GroupMember.objects.create(group=self.g1, user=self.student)
        GroupMember.objects.create(group=g3, user=self.student)
        self.assertEqual(self.student.group_memberships.filter(is_active=True).count(), 2)


class CourseAdminPermissionTests(TestCase):
    """Admin: guruhlarni faqat moderator+ boshqaradi."""

    def setUp(self) -> None:
        self.course = Course.objects.get(slug=seed_data.COURSE["slug"])
        self.moderator = make_user("mod", Role.MODERATOR)
        self.jury_pro = make_user("pro", Role.JURY_PRO)

    def test_moderator_can_open_group_admin(self) -> None:
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.get(reverse("admin:courses_group_changelist")).status_code, 200)

    def test_jury_pro_cannot_open_admin(self) -> None:
        self.client.force_login(self.jury_pro)
        response = self.client.get(reverse("admin:courses_group_changelist"))
        self.assertEqual(response.status_code, 302)  # is_staff yo'q → login sahifasi

    def test_moderator_cannot_edit_lessons(self) -> None:
        self.client.force_login(self.moderator)
        lesson = Lesson.objects.get(number=1)
        self.assertEqual(self.client.get(reverse("admin:courses_lesson_changelist")).status_code, 200)
        response = self.client.post(reverse("admin:courses_lesson_change", args=[lesson.pk]),
                                    {"module": lesson.module_id, "number": 1, "title": "X", "kind": "lesson"})
        self.assertEqual(response.status_code, 403)

    def test_group_creation_in_admin_is_audited(self) -> None:
        self.client.force_login(self.moderator)
        data = {
            "course": self.course.pk, "name": "Python-2", "teacher": self.moderator.pk,
            "start_date": "", "is_active": "on",
            "members-TOTAL_FORMS": "0", "members-INITIAL_FORMS": "0",
            "members-MIN_NUM_FORMS": "0", "members-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("admin:courses_group_add"), data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None))
        group = Group.objects.get(name="Python-2")
        self.assertTrue(AuditLog.objects.filter(action="group_created", object_id=str(group.pk)).exists())
