"""Vazifalar banki testlari: importer, ruxsatlar, markdown, seed sifati."""

import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from audit.models import AuditLog
from courses.models import Lesson
from judge.backends.local import LocalDevBackend

from .importer import ProblemFormatError, parse_problem_dir
from .management.commands.verify_problems import verify_problem
from .markdown import render_markdown
from .models import LessonProblem, Problem

EXAMPLES = settings.BASE_DIR / "docs" / "examples" / "problems"


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password="Sinov-parol-2026", role=role)


class ImporterParseTests(TestCase):
    """problem.yaml tahlili va xatolar."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _copy_example(self, name: str, new_name: str | None = None) -> Path:
        target = self.tmp / (new_name or name)
        shutil.copytree(EXAMPLES / name, target)
        return target

    def test_parse_code_example(self) -> None:
        spec = parse_problem_dir(EXAMPLES / "misol-yigindi")
        self.assertEqual(spec.type, "code")
        self.assertEqual(len(spec.tests), 3)
        self.assertEqual([t.is_sample for t in spec.tests], [True, False, False])
        self.assertIn("print(a + b)", spec.solution)
        self.assertEqual(spec.lessons[0].lesson, 5)

    def test_parse_quiz_and_project_examples(self) -> None:
        quiz = parse_problem_dir(EXAMPLES / "misol-quiz")
        self.assertEqual([q.kind for q in quiz.questions], ["single", "multiple", "text"])
        self.assertEqual(quiz.questions[2].answers, ["5", "besh"])
        project = parse_problem_dir(EXAMPLES / "misol-loyiha")
        self.assertEqual(sum(r.points for r in project.rubric), 100)

    def test_invalid_slug(self) -> None:
        folder = self._copy_example("misol-yigindi", "Yomon_Nom")
        with self.assertRaises(ProblemFormatError):
            parse_problem_dir(folder)

    def test_missing_output_file(self) -> None:
        folder = self._copy_example("misol-yigindi")
        (folder / "tests" / "02.out").unlink()
        with self.assertRaisesMessage(ProblemFormatError, "02.out"):
            parse_problem_dir(folder)

    def test_code_without_tests(self) -> None:
        folder = self._copy_example("misol-yigindi")
        shutil.rmtree(folder / "tests")
        with self.assertRaises(ProblemFormatError):
            parse_problem_dir(folder)

    def test_single_question_needs_exactly_one_correct(self) -> None:
        folder = self._copy_example("misol-quiz")
        meta = folder / "problem.yaml"
        meta.write_text(meta.read_text(encoding="utf-8").replace('- "6"', '- text: "6"\n        correct: true'),
                        encoding="utf-8")
        with self.assertRaisesMessage(ProblemFormatError, "bitta to'g'ri"):
            parse_problem_dir(folder)

    def test_project_requires_rubric(self) -> None:
        folder = self._copy_example("misol-loyiha")
        (folder / "problem.yaml").write_text("title: X\ntype: project\n", encoding="utf-8")
        with self.assertRaises(ProblemFormatError):
            parse_problem_dir(folder)


class ImportCommandTests(TestCase):
    """manage.py import_problems namunaviy papka bilan."""

    def setUp(self) -> None:
        self.author = make_user("ustoz", Role.JURY_PRO)

    def test_import_examples(self) -> None:
        out = StringIO()
        call_command("import_problems", str(EXAMPLES), author="ustoz", stdout=out)
        self.assertIn("3 ta vazifa import qilindi", out.getvalue())
        problem = Problem.objects.get(slug="misol-yigindi")
        self.assertEqual(problem.status, Problem.Status.DRAFT)
        self.assertEqual(problem.author, self.author)
        self.assertEqual(problem.test_cases.count(), 3)
        self.assertEqual(problem.test_cases.first().read_input(), "2 3\n")
        self.assertTrue((Path(settings.MEDIA_ROOT) / "tests" / "misol-yigindi" / "01.in").exists())
        self.assertEqual(Problem.objects.get(slug="misol-quiz").questions.count(), 3)
        self.assertEqual(Problem.objects.get(slug="misol-loyiha").rubric.count(), 3)
        self.assertTrue(LessonProblem.objects.filter(problem=problem, lesson__number=5).exists())
        self.assertTrue(AuditLog.objects.filter(action="problems_imported", actor=self.author).exists())

    def test_reimport_updates_without_duplicates(self) -> None:
        call_command("import_problems", str(EXAMPLES / "misol-yigindi"), author="ustoz", stdout=StringIO())
        call_command("import_problems", str(EXAMPLES / "misol-yigindi"), author="ustoz",
                     status="published", stdout=StringIO())
        self.assertEqual(Problem.objects.filter(slug="misol-yigindi").count(), 1)
        self.assertEqual(Problem.objects.get(slug="misol-yigindi").status, Problem.Status.PUBLISHED)
        self.assertEqual(Problem.objects.get(slug="misol-yigindi").test_cases.count(), 3)

    def test_author_must_be_jury_pro(self) -> None:
        make_user("talaba")
        with self.assertRaises(CommandError):
            call_command("import_problems", str(EXAMPLES), author="talaba", stdout=StringIO())

    def test_imported_example_solution_passes(self) -> None:
        call_command("import_problems", str(EXAMPLES / "misol-yigindi"), author="ustoz", stdout=StringIO())
        ok, info = verify_problem(Problem.objects.get(slug="misol-yigindi"), LocalDevBackend())
        self.assertTrue(ok, info)


class ProblemPermissionTests(TestCase):
    """Ob'ekt darajasidagi ruxsatlar."""

    def setUp(self) -> None:
        self.author = make_user("muallif", Role.JURY_PRO)
        self.other_pro = make_user("boshqa", Role.JURY_PRO)
        self.student = make_user("talaba")
        self.moderator = make_user("mod", Role.MODERATOR)
        self.superadmin = make_user("sa", Role.SUPERADMIN)
        self.draft = Problem.objects.create(slug="qoralama", title="Q", author=self.author)
        self.published = Problem.objects.create(slug="ochiq", title="O", author=self.author,
                                                status=Problem.Status.PUBLISHED)

    def test_view(self) -> None:
        from django.contrib.auth.models import AnonymousUser

        self.assertTrue(self.published.can_view(self.student))
        self.assertTrue(self.published.can_view(AnonymousUser()))
        self.assertFalse(self.draft.can_view(self.student))
        self.assertFalse(self.draft.can_view(self.other_pro))
        self.assertTrue(self.draft.can_view(self.author))
        self.assertTrue(self.draft.can_view(self.moderator))

    def test_hidden_tests_visibility(self) -> None:
        self.assertFalse(self.published.can_view_hidden(self.student))
        self.assertFalse(self.published.can_view_hidden(self.other_pro))
        self.assertTrue(self.published.can_view_hidden(self.author))
        self.assertTrue(self.published.can_view_hidden(self.moderator))

    def test_edit_only_own_for_jury_pro(self) -> None:
        self.assertTrue(self.draft.can_edit(self.author))
        self.assertFalse(self.draft.can_edit(self.other_pro))
        self.assertFalse(self.draft.can_edit(self.moderator))
        self.assertTrue(self.draft.can_edit(self.superadmin))
        self.assertFalse(self.draft.can_edit(self.student))

    def test_author_demoted_loses_edit(self) -> None:
        self.author.role = Role.JURY
        self.author.save()
        self.assertFalse(self.draft.can_edit(self.author))

    def test_publish_requires_moderator(self) -> None:
        self.assertFalse(self.draft.can_publish(self.author))
        self.assertTrue(self.draft.can_publish(self.moderator))


class ProblemAdminTests(TestCase):
    """Admin: moderator nashr etadi, lekin tahrirlay olmaydi."""

    def setUp(self) -> None:
        self.moderator = make_user("mod", Role.MODERATOR)
        self.problem = Problem.objects.create(slug="admin-masala", title="A", author=make_user("pro", Role.JURY_PRO),
                                              status=Problem.Status.REVIEW)
        self.client.force_login(self.moderator)

    def test_moderator_publishes_with_audit(self) -> None:
        response = self.client.post(reverse("admin:problems_problem_changelist"),
                                    {"action": "publish", "_selected_action": [self.problem.pk]})
        self.assertEqual(response.status_code, 302)
        self.problem.refresh_from_db()
        self.assertEqual(self.problem.status, Problem.Status.PUBLISHED)
        log = AuditLog.objects.get(action="problem_published")
        self.assertEqual(log.details, {"old": "review", "new": "published"})

    def test_moderator_cannot_edit_others_problem(self) -> None:
        url = reverse("admin:problems_problem_change", args=[self.problem.pk])
        self.assertEqual(self.client.get(url).status_code, 200)  # faqat ko'rish
        response = self.client.post(url, {"slug": "admin-masala", "title": "O'zgardi"})
        self.assertEqual(response.status_code, 403)


class MarkdownTests(TestCase):
    def test_sanitizes_html(self) -> None:
        html = render_markdown("**qalin** <script>alert(1)</script> [x](javascript:alert(1))")
        self.assertIn("<strong>qalin</strong>", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)

    def test_preserves_latex(self) -> None:
        html = render_markdown("Formula: $a_1 + a_2 \\le 10^9$ va $$x_i^2$$")
        self.assertIn("$a_1 + a_2 \\le 10^9$", html)
        self.assertIn("$$x_i^2$$", html)
        self.assertNotIn("<em>", html)

    def test_code_blocks_and_tables(self) -> None:
        html = render_markdown("```\nprint(1)\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<code>", html)
        self.assertIn("<table>", html)

    def test_empty(self) -> None:
        self.assertEqual(render_markdown(""), "")


class SeedQualityTests(TestCase):
    """Seed kontent MASTER_PROMPT talablariga mos."""

    def test_every_lesson_has_tasks(self) -> None:
        empty = Lesson.objects.filter(lesson_problems__isnull=True)
        self.assertEqual(list(empty.values_list("number", flat=True)), [])

    def test_seed_problems_published_by_nurbek(self) -> None:
        seeds = Problem.objects.filter(is_seed=True)
        self.assertEqual(seeds.count(), 146)
        self.assertFalse(seeds.exclude(status=Problem.Status.PUBLISHED).exists())
        self.assertFalse(seeds.exclude(author__username="nurbek").exists())

    def test_modules_1_2_have_three_code_problems_per_lesson(self) -> None:
        for lesson in Lesson.objects.filter(number__lte=24):
            kinds = sorted(LessonProblem.objects.filter(lesson=lesson, problem__type="code")
                           .values_list("kind", flat=True))
            self.assertEqual(kinds, ["challenge", "classwork", "homework"], lesson)

    def test_code_problems_have_tests_samples_and_solution(self) -> None:
        for problem in Problem.objects.filter(is_seed=True, type="code").prefetch_related("test_cases"):
            tests = list(problem.test_cases.all())
            self.assertGreaterEqual(len(tests), 5, problem.slug)
            self.assertGreaterEqual(sum(t.is_sample for t in tests), 2, problem.slug)
            self.assertGreaterEqual(sum(not t.is_sample for t in tests), 3, problem.slug)
            self.assertTrue(problem.reference_solution.strip(), problem.slug)

    def test_every_lesson_has_five_question_quiz(self) -> None:
        for lesson in Lesson.objects.all():
            quiz = Problem.objects.get(lesson_links__lesson=lesson, type="quiz")
            self.assertEqual(quiz.questions.count(), 5, lesson)

    def test_modules_3_4_and_defenses_have_projects(self) -> None:
        numbers = list(range(25, 49)) + [12, 24]
        for lesson in Lesson.objects.filter(number__in=numbers):
            project = Problem.objects.get(lesson_links__lesson=lesson, type="project")
            self.assertEqual(sum(project.rubric.values_list("max_points", flat=True)), project.points, lesson)

    def test_all_seed_solutions_pass_on_local_backend(self) -> None:
        backend = LocalDevBackend()
        failures = []
        for problem in Problem.objects.filter(is_seed=True, type="code").prefetch_related("test_cases"):
            ok, info = verify_problem(problem, backend)
            if not ok:
                failures.append(f"{problem.slug}: {info}")
        self.assertEqual(failures, [])
