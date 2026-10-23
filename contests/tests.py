"""Kontestlar testlari: ICPC/IOI hisoblash, muzlatish, ko'rinish, ro'yxatdan o'tish, yuborish va reyting."""

from datetime import timedelta
from io import StringIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from audit.models import AuditLog
from courses.models import Group, GroupMember
from judge.types import Verdict
from problems.models import Problem
from submissions.models import Submission

from .models import Contest, ContestParticipant, ContestProblem, RatingHistory
from .services import apply_due_ratings, apply_ratings, register, scoreboard

PASSWORD = "Sinov-parol-2026"


def make_user(username: str, role: int = Role.USER) -> User:
    return User.objects.create_user(username=username, password=PASSWORD, role=role)


class ContestFixture(TestCase):
    """Kontest yaratish va yechim qo'shish yordamchilari."""

    def setUp(self) -> None:
        self.jury = make_user("jury", Role.JURY)
        self.a = Problem.objects.get(slug="l05-salom")      # 100 ball
        self.b = Problem.objects.get(slug="l05-ikki-son")   # 100 ball

    def make_contest(self, started_minutes_ago: int = 30, duration: int = 120, **extra) -> Contest:
        contest = Contest.objects.create(
            title="Sinov", slug=extra.pop("slug", "sinov"), owner=self.jury, duration_minutes=duration,
            start_at=timezone.now() - timedelta(minutes=started_minutes_ago), **extra)
        ContestProblem.objects.create(contest=contest, problem=self.a, label="A", points=50)
        ContestProblem.objects.create(contest=contest, problem=self.b, label="B", points=100)
        return contest

    def join(self, contest: Contest, *users: User) -> None:
        for user in users:
            ContestParticipant.objects.create(contest=contest, user=user)

    def sub(self, contest: Contest, user: User, problem: Problem, verdict: str, minute: float,
            score: int | None = None, status: str = Submission.Status.DONE) -> Submission:
        submission = Submission.objects.create(
            user=user, problem=problem, contest=contest, code="x", status=status, verdict=verdict,
            score=score if score is not None else (problem.points if verdict == Verdict.ACCEPTED else 0))
        Submission.objects.filter(pk=submission.pk).update(created_at=contest.start_at + timedelta(minutes=minute))
        return submission


class IcpcScoreboardTests(ContestFixture):
    def test_solved_penalty_and_rank(self) -> None:
        contest = self.make_contest()
        u1, u2 = make_user("u1"), make_user("u2")
        self.join(contest, u1, u2)
        self.sub(contest, u1, self.a, Verdict.WRONG_ANSWER, 5)
        self.sub(contest, u1, self.a, Verdict.ACCEPTED, 10)
        self.sub(contest, u1, self.b, Verdict.ACCEPTED, 30)
        self.sub(contest, u2, self.a, Verdict.ACCEPTED, 3)
        self.sub(contest, u2, self.b, Verdict.COMPILATION_ERROR, 4)  # jarimasiz
        self.sub(contest, u2, self.b, Verdict.WRONG_ANSWER, 6)
        self.sub(contest, u2, self.b, Verdict.ACCEPTED, 50)
        rows = scoreboard(contest).rows
        self.assertEqual([(r.user.username, r.rank, r.solved, r.penalty) for r in rows],
                         [("u1", 1, 2, 60), ("u2", 2, 2, 73)])
        self.assertTrue(rows[1].cells["A"].first_solver)
        self.assertTrue(rows[0].cells["B"].first_solver)
        self.assertEqual(rows[1].cells["B"].attempts, 1)

    def test_attempts_after_accept_ignored_and_ties(self) -> None:
        contest = self.make_contest()
        u1, u2, u3 = make_user("u1"), make_user("u2"), make_user("u3")
        self.join(contest, u1, u2, u3)
        self.sub(contest, u1, self.a, Verdict.ACCEPTED, 10)
        self.sub(contest, u1, self.a, Verdict.WRONG_ANSWER, 11)
        self.sub(contest, u2, self.a, Verdict.ACCEPTED, 10)
        rows = scoreboard(contest).rows
        self.assertEqual([(r.user.username, r.rank, r.penalty) for r in rows],
                         [("u1", 1, 10), ("u2", 1, 10), ("u3", 3, 0)])

    def test_non_participants_and_pending(self) -> None:
        contest = self.make_contest()
        u1, outsider = make_user("u1"), make_user("begona")
        self.join(contest, u1)
        self.sub(contest, outsider, self.a, Verdict.ACCEPTED, 1)
        self.sub(contest, u1, self.a, "", 2, status=Submission.Status.QUEUED)
        rows = scoreboard(contest).rows
        self.assertEqual([r.user.username for r in rows], ["u1"])
        self.assertEqual((rows[0].solved, rows[0].cells["A"].pending), (0, 1))


class IoiScoreboardTests(ContestFixture):
    def test_best_partial_scores_scaled(self) -> None:
        contest = self.make_contest(scoring=Contest.Scoring.IOI)
        u1, u2 = make_user("u1"), make_user("u2")
        self.join(contest, u1, u2)
        self.sub(contest, u1, self.a, Verdict.WRONG_ANSWER, 1, score=40)
        self.sub(contest, u1, self.a, Verdict.WRONG_ANSWER, 2, score=80)
        self.sub(contest, u1, self.a, Verdict.WRONG_ANSWER, 3, score=20)
        self.sub(contest, u2, self.b, Verdict.ACCEPTED, 5)
        rows = scoreboard(contest).rows
        self.assertEqual([(r.user.username, r.rank, r.score) for r in rows], [("u2", 1, 100), ("u1", 2, 40)])
        self.assertEqual(rows[1].cells["A"].score, 40)  # 80/100 × 50


class FreezeTests(ContestFixture):
    def setUp(self) -> None:
        super().setUp()
        # 100 daqiqa oldin boshlangan, 120 daqiqa, oxirgi 30 daqiqa muzlatilgan → hozir muzlatish vaqti
        self.contest = self.make_contest(started_minutes_ago=100, freeze_minutes=30)
        self.student = make_user("talaba")
        self.join(self.contest, self.student)
        self.sub(self.contest, self.student, self.a, Verdict.ACCEPTED, 95)  # muzlatishdan keyin

    def test_hidden_for_participants(self) -> None:
        board = scoreboard(self.contest, self.student)
        self.assertTrue(board.frozen)
        cell = board.rows[0].cells["A"]
        self.assertEqual((cell.solved, cell.pending), (False, 1))

    def test_visible_for_manager(self) -> None:
        board = scoreboard(self.contest, self.jury)
        self.assertFalse(board.frozen)
        self.assertTrue(board.rows[0].cells["A"].solved)

    def test_unfrozen_after_end(self) -> None:
        board = scoreboard(self.contest, self.student, now=self.contest.end_at + timedelta(seconds=1))
        self.assertFalse(board.frozen)
        self.assertTrue(board.rows[0].cells["A"].solved)


class VisibilityAndRegistrationTests(ContestFixture):
    def test_group_contest_visible_only_to_members(self) -> None:
        group = Group.objects.get(name="Python-1")
        contest = self.make_contest(visibility=Contest.Visibility.GROUP, group=group)
        member, outsider = make_user("azo"), make_user("begona")
        GroupMember.objects.create(group=group, user=member)
        self.assertTrue(contest.can_view(member))
        self.assertFalse(contest.can_view(outsider))
        self.assertTrue(contest.can_view(self.jury))
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse("contest_detail", args=[contest.slug])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("contest_list")), contest.title)

    def test_password_contest(self) -> None:
        contest = self.make_contest(visibility=Contest.Visibility.PASSWORD)
        contest.set_password("maxfiy")
        contest.save()
        user = make_user("talaba")
        with self.assertRaises(ValidationError):
            register(user, contest, "noto'g'ri")
        register(user, contest, "maxfiy")
        self.assertTrue(contest.is_participant(user))
        self.assertNotEqual(contest.password_hash, "maxfiy")

    def test_cannot_register_after_finish(self) -> None:
        contest = self.make_contest(started_minutes_ago=200, duration=60)
        with self.assertRaises(PermissionDenied):
            register(make_user("kech"), contest)

    def test_problems_visibility_timeline(self) -> None:
        upcoming = self.make_contest(started_minutes_ago=-60, slug="kelgusi")
        participant, other = make_user("ishtirokchi"), make_user("boshqa")
        self.join(upcoming, participant)
        self.assertFalse(upcoming.can_see_problems(participant))
        self.assertTrue(upcoming.can_see_problems(self.jury))
        running = self.make_contest(slug="joriy")
        self.join(running, participant)
        self.assertTrue(running.can_see_problems(participant))
        self.assertFalse(running.can_see_problems(other))
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("contest_problem", args=["joriy", "A"])).status_code, 403)
        finished = self.make_contest(started_minutes_ago=300, slug="tugagan")
        self.assertTrue(finished.can_see_problems(other))

    def test_register_view(self) -> None:
        contest = self.make_contest(started_minutes_ago=-10)
        self.client.force_login(make_user("talaba"))
        response = self.client.post(reverse("contest_register", args=[contest.slug]), follow=True)
        self.assertContains(response, "ro‘yxatdan o‘tgansiz")
        self.assertEqual(contest.participants.count(), 1)


class ContestSubmitTests(ContestFixture):
    def test_submit_during_contest(self) -> None:
        contest = self.make_contest()
        user = make_user("talaba")
        self.join(contest, user)
        self.client.force_login(user)
        response = self.client.post(reverse("contest_submit", args=[contest.slug, "a"]), {"code": "print(1)"})
        submission = Submission.objects.get()
        self.assertRedirects(response, reverse("submission_detail", args=[submission.pk]))
        self.assertEqual((submission.contest, submission.problem), (contest, self.a))

    def test_non_participant_forbidden(self) -> None:
        contest = self.make_contest()
        self.client.force_login(make_user("begona"))
        response = self.client.post(reverse("contest_submit", args=[contest.slug, "A"]), {"code": "print(1)"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Submission.objects.exists())

    def test_submit_outside_contest_time(self) -> None:
        contest = self.make_contest(started_minutes_ago=-30)
        user = make_user("talaba")
        self.join(contest, user)
        self.client.force_login(user)
        self.client.post(reverse("contest_submit", args=[contest.slug, "A"]), {"code": "print(1)"})
        self.assertFalse(Submission.objects.exists())

    def test_draft_problem_usable_in_contest(self) -> None:
        pro = make_user("pro", Role.JURY_PRO)
        draft = Problem.objects.create(slug="yopiq-masala", title="Yopiq", author=pro, type="code")
        contest = self.make_contest()
        ContestProblem.objects.create(contest=contest, problem=draft, label="C")
        user = make_user("talaba")
        self.join(contest, user)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("contest_problem", args=[contest.slug, "C"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("problem_detail", args=["yopiq-masala"])).status_code, 404)
        self.client.post(reverse("contest_submit", args=[contest.slug, "C"]), {"code": "print(1)"})
        self.assertEqual(Submission.objects.get().problem, draft)

    def test_code_opens_after_contest(self) -> None:
        contest = self.make_contest()
        author, other = make_user("muallif"), make_user("boshqa")
        self.join(contest, author)
        submission = self.sub(contest, author, self.a, Verdict.WRONG_ANSWER, 1)
        self.assertFalse(submission.can_view_code(other))
        Contest.objects.filter(pk=contest.pk).update(start_at=timezone.now() - timedelta(days=1))
        submission = Submission.objects.select_related("contest").get(pk=submission.pk)
        self.assertTrue(submission.can_view_code(other))


class RatingApplicationTests(ContestFixture):
    def setUp(self) -> None:
        super().setUp()
        self.contest = self.make_contest(started_minutes_ago=300, is_rated=True)
        self.winner, self.loser, self.idle = make_user("g"), make_user("m"), make_user("q")
        self.join(self.contest, self.winner, self.loser, self.idle)
        self.sub(self.contest, self.winner, self.a, Verdict.ACCEPTED, 5)
        self.sub(self.contest, self.loser, self.a, Verdict.WRONG_ANSWER, 5)

    def test_ratings_applied_once(self) -> None:
        deltas = apply_ratings(self.contest)
        self.winner.refresh_from_db()
        self.loser.refresh_from_db()
        self.idle.refresh_from_db()
        self.assertGreater(self.winner.rating, 1200)
        self.assertLess(self.loser.rating, 1200)
        self.assertEqual(self.idle.rating, 1200)  # yechim yubormagan — hisobga olinmaydi
        self.assertEqual(set(deltas), {self.winner.pk, self.loser.pk})
        history = RatingHistory.objects.get(user=self.winner)
        self.assertEqual((history.old_rating, history.rank), (1200, 1))
        self.assertEqual(apply_ratings(self.contest), {})
        self.assertEqual(RatingHistory.objects.count(), 2)
        self.assertTrue(AuditLog.objects.filter(action="contest_ratings_applied").exists())

    def test_waits_for_pending_submissions(self) -> None:
        self.sub(self.contest, self.loser, self.b, "", 10, status=Submission.Status.QUEUED)
        with self.assertRaises(ValidationError):
            apply_ratings(self.contest)
        self.assertEqual(apply_due_ratings(), 0)

    def test_not_finished_or_unrated(self) -> None:
        running = self.make_contest(slug="joriy", is_rated=True)
        with self.assertRaises(ValidationError):
            apply_ratings(running)
        unrated = self.make_contest(started_minutes_ago=300, slug="oddiy")
        self.assertEqual(apply_ratings(unrated), {})

    def test_worker_applies_due_ratings(self) -> None:
        out = StringIO()
        call_command("run_judge_worker", once=True, stdout=out)
        self.assertIn("1 ta kontest reytingi hisoblandi", out.getvalue())
        self.contest.refresh_from_db()
        self.assertTrue(self.contest.ratings_applied)

    def test_profile_shows_rating_graph(self) -> None:
        apply_ratings(self.contest)
        response = self.client.get(reverse("profile", args=["g"]))
        self.assertContains(response, "<polyline")
        self.assertContains(response, self.contest.title)


class ContestPanelTests(ContestFixture):
    def _form(self, **extra) -> dict:
        data = {"title": "Yangi", "slug": "yangi", "description": "", "start_at": "2030-01-01T10:00",
                "duration_minutes": 90, "scoring": "icpc", "penalty_minutes": 20, "freeze_minutes": 0,
                "visibility": "public", "group": "", "is_rated": "on", "password": ""}
        data.update(extra)
        return data

    def test_jury_creates_unrated_contest(self) -> None:
        self.client.force_login(self.jury)
        response = self.client.post(reverse("panel:contest_create"), self._form())
        self.assertRedirects(response, reverse("panel:contest_edit", args=["yangi"]))
        contest = Contest.objects.get(slug="yangi")
        self.assertEqual(contest.owner, self.jury)
        self.assertFalse(contest.is_rated)  # reytingni faqat moderator yoqadi

    def test_password_required_and_hashed(self) -> None:
        self.client.force_login(self.jury)
        response = self.client.post(reverse("panel:contest_create"), self._form(visibility="password"))
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse("panel:contest_create"), self._form(visibility="password", password="sir123"))
        contest = Contest.objects.get(slug="yangi")
        self.assertTrue(contest.check_password("sir123"))

    def test_jury_manages_only_own_contests(self) -> None:
        contest = self.make_contest()
        other_jury = make_user("jury2", Role.JURY)
        self.client.force_login(other_jury)
        self.assertEqual(self.client.get(reverse("panel:contest_edit", args=[contest.slug])).status_code, 403)
        self.assertNotIn(contest, self.client.get(reverse("panel:contests")).context["contests"])
        self.client.force_login(make_user("mod", Role.MODERATOR))
        self.assertEqual(self.client.get(reverse("panel:contest_edit", args=[contest.slug])).status_code, 200)

    def test_student_cannot_open_contest_panel(self) -> None:
        self.client.force_login(make_user("talaba"))
        self.assertEqual(self.client.get(reverse("panel:contests")).status_code, 403)

    def test_add_and_remove_problems(self) -> None:
        contest = self.make_contest(started_minutes_ago=-60)
        self.client.force_login(self.jury)
        url = reverse("panel:contest_problem_add", args=[contest.slug])
        self.client.post(url, {"slug": "l08-baho", "label": "c", "points": 100})
        self.assertTrue(contest.problems.filter(label="C", problem__slug="l08-baho").exists())
        self.client.post(url, {"slug": "l10-yigindi", "label": "C", "points": 100})  # harf band
        self.assertEqual(contest.problems.count(), 3)
        draft = Problem.objects.create(slug="begona-qoralama", title="Q", author=make_user("pro", Role.JURY_PRO))
        self.client.post(url, {"slug": draft.slug, "label": "D", "points": 100})
        self.assertFalse(contest.problems.filter(problem=draft).exists())  # boshqaning qoralamasi
        link = contest.problems.get(label="C")
        self.client.post(reverse("panel:contest_problem_remove", args=[contest.slug, link.pk]))
        self.assertFalse(contest.problems.filter(label="C").exists())

    def test_cannot_remove_problem_with_submissions(self) -> None:
        contest = self.make_contest()
        user = make_user("talaba")
        self.join(contest, user)
        self.sub(contest, user, self.a, Verdict.ACCEPTED, 1)
        self.client.force_login(self.jury)
        link = contest.problems.get(label="A")
        self.client.post(reverse("panel:contest_problem_remove", args=[contest.slug, link.pk]))
        self.assertTrue(contest.problems.filter(label="A").exists())


class ContestPagesTests(ContestFixture):
    def test_seed_contest(self) -> None:
        contest = Contest.objects.get(slug="kirish-kontesti")
        self.assertEqual(list(contest.problems.values_list("label", flat=True)), ["A", "B", "C", "D"])
        self.assertEqual(contest.owner.username, "nurbek")

    def test_pages_render(self) -> None:
        contest = self.make_contest()
        user = make_user("talaba")
        self.join(contest, user)
        self.sub(contest, user, self.a, Verdict.ACCEPTED, 3)
        self.client.force_login(user)
        for url in (reverse("contest_list"), reverse("contest_detail", args=[contest.slug]),
                    reverse("contest_scoreboard", args=[contest.slug]),
                    reverse("contest_problem", args=[contest.slug, "B"])):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        partial = self.client.get(reverse("contest_scoreboard", args=[contest.slug]) + "?partial=1")
        self.assertContains(partial, 'hx-trigger="every 15s"')
        self.assertNotContains(partial, "<html")
        self.assertContains(partial, "talaba")
