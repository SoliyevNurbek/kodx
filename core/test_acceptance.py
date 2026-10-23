"""
Yakuniy qabul (MASTER_PROMPT §5) — uchta to'liq ssenariy oxiridan-oxirigacha, haqiqiy view'lar va judge worker bilan.
"""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from contests.models import Contest
from courses.models import Group, GroupMember, Lesson
from judge.types import Verdict
from problems.models import Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

PASSWORD = "Juda-kuchli-parol-77"


def worker() -> None:
    call_command("run_judge_worker", once=True, stdout=StringIO())


class AcceptanceTests(TestCase):
    def setUp(self) -> None:
        self.teacher = User.objects.create_user("ustoz", password=PASSWORD, role=Role.MODERATOR)
        self.group = Group.objects.get(name="Python-1")

    def _register(self, username: str):
        self.client.logout()
        response = self.client.post(reverse("register"), {
            "username": username, "first_name": username.title(), "last_name": "", "email": "",
            "password1": PASSWORD, "password2": PASSWORD})
        self.assertEqual(response.status_code, 302)
        return User.objects.get(username=username)

    def test_1_student_journey(self) -> None:
        """Ro'yxatdan o'tadi → guruhga qo'shiladi → masala, test va loyiha → ball → reytingda o'rni."""
        student = self._register("lola")
        GroupMember.objects.create(group=self.group, user=student)
        lesson = Lesson.objects.get(number=5)

        self.client.post(reverse("submit_code", args=["l05-ikki-son"]),
                         {"code": "a = int(input())\nb = int(input())\nprint(a + b)\n", "lesson": lesson.pk})
        worker()
        submission = Submission.objects.get(user=student)
        self.assertEqual((submission.verdict, submission.score), (Verdict.ACCEPTED, 100))
        self.assertContains(self.client.get(reverse("submission_detail", args=[submission.pk])), "Qabul qilindi")

        quiz = Problem.objects.get(slug="l05-quiz")
        answers = {}
        for q in quiz.questions.prefetch_related("options"):
            answers[f"q{q.order}"] = (q.accepted_answers()[0] if q.kind == "text"
                                      else [str(o.order) for o in q.options.all() if o.is_correct])
        self.client.post(reverse("submit_quiz", args=[quiz.slug]), answers)
        self.assertEqual(QuizAttempt.objects.get(user=student).score, 5)

        self.client.post(reverse("submit_project", args=["l12-loyiha-1"]),
                         {"github_url": "https://github.com/lola/oyin"})
        project = ProjectSubmission.objects.get(user=student)

        self.client.force_login(self.teacher)
        rubric = {f"c{c.order}": c.max_points for c in project.problem.rubric.all()}
        self.client.post(reverse("panel:project_grade", args=[project.pk]), rubric | {"feedback": "A’lo"})

        self.client.force_login(student)
        lesson_page = self.client.get(reverse("lesson_detail", args=[lesson.module.course.slug, 5]))
        self.assertContains(lesson_page, "badge-solved")
        board = self.client.get(reverse("leaderboard"))
        self.assertEqual(board.context["me"]["place"], 1)
        self.assertEqual(board.context["me"]["score"], 100 + 50 + 100)
        self.assertContains(self.client.get(reverse("profile", args=["lola"])), "Birinchi qadam")

    def test_2_teacher_progress_grades_csv(self) -> None:
        """O'qituvchi progress va baholarni ko'radi, loyihani baholaydi, CSV eksport qiladi."""
        student = User.objects.create_user("bek", password=PASSWORD)
        GroupMember.objects.create(group=self.group, user=student)
        Submission.objects.create(user=student, problem=Problem.objects.get(slug="l05-salom"), code="x",
                                  status="done", verdict=Verdict.ACCEPTED, score=100)
        self.client.force_login(self.teacher)
        self.client.post(reverse("panel:group_attendance", args=[self.group.pk]),
                         {"lesson": 5, "present": [str(student.pk)]})
        progress = self.client.get(reverse("panel:group_progress", args=[self.group.pk]))
        self.assertEqual(progress.context["rows"][0]["total"], 1)
        grades = self.client.get(reverse("panel:group_grades", args=[self.group.pk]))
        module1 = grades.context["grades"][0][1].modules[0]
        self.assertGreater(module1.attendance, 0)
        self.assertGreater(module1.tasks, 0)
        csv = self.client.get(reverse("panel:group_grades", args=[self.group.pk]) + "?format=csv")
        self.assertIn("bek,", csv.content.decode("utf-8-sig"))

    def test_3_jury_contest_rating(self) -> None:
        """Jury kontest o'tkazadi, jadval ishlaydi, reyting yangilanadi."""
        jury = User.objects.create_user("hakam", password=PASSWORD, role=Role.JURY)
        self.client.force_login(jury)
        self.client.post(reverse("panel:contest_create"), {
            "title": "Sinov kontest", "slug": "sinov-kontest", "description": "",
            "start_at": (timezone.localtime() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": 60, "scoring": "icpc", "penalty_minutes": 20, "freeze_minutes": 0,
            "visibility": "public", "group": ""})
        contest = Contest.objects.get(slug="sinov-kontest")
        self.client.post(reverse("panel:contest_problem_add", args=[contest.slug]),
                         {"slug": "l05-ikki-son", "label": "A", "points": 100})
        Contest.objects.filter(pk=contest.pk).update(is_rated=True)  # reytingni moderator yoqadi

        codes = {"g1": "a = int(input())\nb = int(input())\nprint(a + b)\n", "g2": "print(0)\n"}
        for username, code in codes.items():
            user = User.objects.create_user(username, password=PASSWORD)
            self.client.force_login(user)
            self.client.post(reverse("contest_register", args=[contest.slug]))
            self.client.post(reverse("contest_submit", args=[contest.slug, "A"]), {"code": code})
        worker()
        board = self.client.get(reverse("contest_scoreboard", args=[contest.slug])).context["board"]
        self.assertEqual([(r.user.username, r.rank, r.solved) for r in board.rows], [("g1", 1, 1), ("g2", 2, 0)])

        # Vaqtni «oldinga suramiz»: kontest va yechimlar 2 soat oldin bo'lgandek (nisbiy tartib saqlanadi)
        shift = timedelta(hours=2)
        Contest.objects.filter(pk=contest.pk).update(start_at=contest.start_at - shift)
        for submission in Submission.objects.filter(contest=contest):
            Submission.objects.filter(pk=submission.pk).update(created_at=submission.created_at - shift)
        worker()  # bo'sh worker tugagan reytingli kontest reytingini hisoblaydi
        self.assertGreater(User.objects.get(username="g1").rating, 1200)
        self.assertLess(User.objects.get(username="g2").rating, 1200)
        self.assertContains(self.client.get(reverse("profile", args=["g1"])), "<polyline")
