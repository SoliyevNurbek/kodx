"""
`manage.py seed_demo` — demo ma'lumotlar (FAQAT DEBUG uchun): 20 ta o'quvchi, urinishlar, quiz va loyihalar,
davomat, tugagan reytingli kontest va reyting.

Barcha demo foydalanuvchilar `demo` bilan boshlanadi; `--reset` ularni (va demo kontestini) o'chirib qayta yaratadi.
Demo akkauntlarga standart holatda kirib bo'lmaydi; `--password` bilan umumiy parol berish mumkin.
"""

import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from contests.models import Contest, ContestParticipant, ContestProblem
from contests.services import apply_ratings
from courses.models import Course, Group, GroupMember, Lesson
from grading.models import Attendance
from grading.practice import refresh_practice_stats
from judge.types import Verdict
from problems.models import Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

FIRST_NAMES = ["Ali", "Vali", "Nodira", "Dilnoza", "Jasur", "Malika", "Sardor", "Zarina", "Bekzod", "Madina",
               "Otabek", "Shahzoda", "Aziz", "Kamola", "Javohir", "Sevara", "Doston", "Gulnoza", "Sherzod", "Nilufar"]
DEMO_PREFIX = "demo"
DEMO_CONTEST = "demo-kontest"


class Command(BaseCommand):
    help = "Demo ma'lumotlar: 20 o'quvchi, urinishlar, kontest va reyting (faqat DEBUG)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--students", type=int, default=20)
        parser.add_argument("--seed", type=int, default=42, help="Tasodifiylik urug'i (takrorlanuvchan natija)")
        parser.add_argument("--password", default="", help="Demo akkauntlar uchun umumiy parol (ixtiyoriy)")
        parser.add_argument("--reset", action="store_true", help="Eski demo ma'lumotlarni o'chirib qayta yaratish")

    def handle(self, *args, students: int, seed: int, password: str, reset: bool, **options) -> None:
        if not (settings.DEBUG or getattr(settings, "TESTING", False)):
            raise CommandError("seed_demo faqat DEBUG=True da ishlaydi.")
        if User.objects.filter(username__startswith=DEMO_PREFIX).exists():
            if not reset:
                raise CommandError("Demo ma'lumotlar allaqachon bor. Qayta yaratish uchun: --reset")
            Contest.objects.filter(slug=DEMO_CONTEST).delete()
            User.objects.filter(username__startswith=DEMO_PREFIX).delete()
        rng = random.Random(seed)
        with transaction.atomic():
            users = self._users(students, password)
            self._course_activity(rng, users)
            contest = self._contest(rng, users)
        apply_ratings(contest)
        for user in users:
            refresh_practice_stats(user)
        self.stdout.write(self.style.SUCCESS(
            f"{len(users)} ta demo o'quvchi, {Submission.objects.filter(user__in=users).count()} ta yechim, "
            f"kontest «{contest.title}» va reyting yaratildi."))

    def _users(self, count: int, password: str) -> list[User]:
        users = []
        for index in range(count):
            user = User(username=f"{DEMO_PREFIX}{index + 1:02d}", first_name=FIRST_NAMES[index % len(FIRST_NAMES)],
                        is_seed=True)
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save()
            users.append(user)
        return users

    def _course_activity(self, rng: random.Random, users: list[User]) -> None:
        course = Course.objects.filter(is_active=True).first()
        teacher = User.objects.filter(role__gte=4, is_active=True).order_by("pk").first()
        group, _ = Group.objects.get_or_create(course=course, name="Demo-guruh", defaults={"teacher": teacher})
        lessons = list(Lesson.objects.filter(module__course=course, number__lte=16).order_by("number"))
        code = list(Problem.objects.filter(type="code", status="published", lesson_links__lesson__in=lessons))
        quizzes = list(Problem.objects.filter(type="quiz", lesson_links__lesson__in=lessons))
        projects = list(Problem.objects.filter(type="project", lesson_links__lesson__number__in=[12]))
        now = timezone.now()
        for user in users:
            GroupMember.objects.create(group=group, user=user)
            skill = rng.uniform(0.3, 0.95)  # o'quvchi «kuchi»
            for problem in rng.sample(code, k=min(len(code), rng.randint(8, 35))):
                when = now - timedelta(days=rng.randint(0, 40), minutes=rng.randint(0, 600))
                for attempt in range(rng.randint(1, 3)):
                    accepted = rng.random() < skill or attempt == 2
                    verdict = Verdict.ACCEPTED if accepted else rng.choice(
                        [Verdict.WRONG_ANSWER, Verdict.RUNTIME_ERROR, Verdict.TIME_LIMIT])
                    self._submission(user, problem, verdict, when + timedelta(minutes=attempt * 7),
                                     problem.points if accepted else rng.randint(0, problem.points // 2))
                    if accepted:
                        break
            for quiz in rng.sample(quizzes, k=min(len(quizzes), rng.randint(3, 12))):
                score = sum(1 for _ in range(5) if rng.random() < skill)
                attempt = QuizAttempt.objects.create(user=user, problem=quiz, score=score, max_score=5)
                QuizAttempt.objects.filter(pk=attempt.pk).update(created_at=now - timedelta(days=rng.randint(0, 40)))
            for project in projects:
                if rng.random() < 0.7:
                    ProjectSubmission.objects.create(
                        user=user, problem=project, github_url=f"https://github.com/{user.username}/loyiha-1",
                        status="graded", score=int(skill * 100), graded_by=teacher, graded_at=now, feedback="Demo baho")
            for lesson in lessons:
                Attendance.objects.create(group=group, lesson=lesson, user=user, present=rng.random() < 0.9,
                                          marked_by=teacher)

    def _submission(self, user, problem, verdict, when, score: int, contest=None) -> None:
        submission = Submission.objects.create(user=user, problem=problem, contest=contest, code="# demo yechim\n",
                                               status=Submission.Status.DONE, verdict=verdict, score=score,
                                               time_ms=random.randint(20, 400), judged_at=when)
        Submission.objects.filter(pk=submission.pk).update(created_at=when)

    def _contest(self, rng: random.Random, users: list[User]) -> Contest:
        owner = User.objects.filter(role__gte=4, is_active=True).order_by("pk").first()
        start = timezone.now() - timedelta(days=3)
        contest = Contest.objects.create(title="Demo kontest", slug=DEMO_CONTEST, owner=owner, start_at=start,
                                         duration_minutes=120, scoring=Contest.Scoring.ICPC, is_rated=True,
                                         description="Demo ma'lumot uchun tugagan reytingli kontest.")
        problems = list(Problem.objects.filter(slug__in=["l07-kabisa-yili", "l09-kalkulyator", "l10-tub-sonlar",
                                                         "l11-kollats", "l12-bankomat"]))
        for label, problem in zip("ABCDE", problems, strict=False):
            ContestProblem.objects.create(contest=contest, problem=problem, label=label)
        for user in users:
            ContestParticipant.objects.create(contest=contest, user=user)
            for problem in problems:
                if rng.random() < 0.6:
                    for _ in range(rng.randint(0, 2)):
                        self._submission(user, problem, Verdict.WRONG_ANSWER,
                                         start + timedelta(minutes=rng.randint(1, 60)), 0, contest)
                    self._submission(user, problem, Verdict.ACCEPTED, start + timedelta(minutes=rng.randint(61, 119)),
                                     problem.points, contest)
        return contest
