"""Management buyruqlari testlari: seed_demo, init_superuser, verify_problems, reyting va statistika."""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from accounts.models import Role, User
from audit.models import AuditLog
from contests.models import Contest, RatingHistory
from grading.models import PracticeStats
from problems.models import Problem
from submissions.models import Submission


def run(command: str, *args, **kwargs) -> str:
    out = StringIO()
    call_command(command, *args, stdout=out, **kwargs)
    return out.getvalue()


class SeedDemoTests(TestCase):
    def test_creates_demo_data(self) -> None:
        output = run("seed_demo", students=5)
        self.assertIn("5 ta demo o'quvchi", output)
        demo = User.objects.filter(username__startswith="demo")
        self.assertEqual(demo.count(), 5)
        self.assertFalse(any(u.has_usable_password() for u in demo))
        self.assertTrue(Submission.objects.filter(user__in=demo).exists())
        contest = Contest.objects.get(slug="demo-kontest")
        self.assertTrue(contest.ratings_applied)
        self.assertTrue(RatingHistory.objects.filter(contest=contest).exists())
        self.assertEqual(PracticeStats.objects.filter(user__in=demo).count(), 5)

    def test_requires_reset_and_is_deterministic(self) -> None:
        run("seed_demo", students=3, seed=7)
        first = Submission.objects.filter(user__username__startswith="demo", contest=None).count()
        with self.assertRaises(CommandError):
            run("seed_demo", students=3)
        run("seed_demo", students=3, seed=7, reset=True)
        self.assertEqual(User.objects.filter(username__startswith="demo").count(), 3)
        self.assertEqual(Submission.objects.filter(user__username__startswith="demo", contest=None).count(), first)
        self.assertEqual(Contest.objects.filter(slug="demo-kontest").count(), 1)

    def test_password_option(self) -> None:
        run("seed_demo", students=2, password="Demo-parol-2026")
        self.assertTrue(User.objects.get(username="demo01").check_password("Demo-parol-2026"))

    @override_settings(DEBUG=False, TESTING=False)
    def test_refuses_without_debug(self) -> None:
        with self.assertRaises(CommandError):
            run("seed_demo", students=1)


class InitSuperuserTests(TestCase):
    def test_sets_password_only_in_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text("SECRET_KEY=x\n", encoding="utf-8")
            output = run("init_superuser", env_file=str(env))
            content = env.read_text(encoding="utf-8")
        password = content.strip().splitlines()[-1].split("=", 1)[1]
        self.assertEqual(len(password), 20)
        self.assertNotIn(password, output)
        user = User.objects.get(username="nurbek")  # seed'da bor edi — yangilandi
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.must_change_password)
        self.assertEqual(user.role, Role.SUPERADMIN)
        log = AuditLog.objects.get(action="superuser_initialized")
        self.assertNotIn(password, str(log.details))

    def test_missing_env_file(self) -> None:
        with self.assertRaises(CommandError):
            run("init_superuser", env_file="Z:/yoq/.env")


class OtherCommandTests(TestCase):
    def test_verify_problems(self) -> None:
        self.assertIn("barchasi o'tdi", run("verify_problems", slug=["l05-salom", "l06-vaqt-formati"]))
        problem = Problem.objects.get(slug="l05-salom")
        problem.reference_solution = "print('xato')\n"
        problem.save()
        with self.assertRaises(CommandError):
            run("verify_problems", slug=["l05-salom"])
        problem.reference_solution = ""
        problem.save()
        with self.assertRaises(CommandError):
            run("verify_problems", slug=["l05-salom"])

    def test_apply_contest_ratings_and_recalculate(self) -> None:
        self.assertIn("0 ta kontest", run("apply_contest_ratings"))
        user = User.objects.create_user("ali", password="Sinov-parol-2026")
        Submission.objects.create(user=user, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  verdict="AC", status="done", score=100)
        self.assertIn("ta foydalanuvchi yangilandi", run("recalculate_practice"))
        self.assertEqual(PracticeStats.objects.get(user=user).score, 100)
