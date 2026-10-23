"""Bosh sahifa (landing hero) testlari: sidebar, statistika, CTA havolalari, hero surati."""

from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Role, User
from courses.models import Course
from judge.types import Verdict
from problems.models import Problem
from submissions.models import Submission
from submissions.stats import site_counters

from .models import SiteSettings

PASSWORD = "Sinov-parol-2026"
IMG_DIR = Path(settings.BASE_DIR) / "static" / "img"


def make_user(username: str, role: int = Role.USER, **extra) -> User:
    return User.objects.create_user(username=username, password=PASSWORD, role=role, **extra)


class HomeTestCase(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def home(self):
        return self.client.get(reverse("home"))


class SidebarTests(HomeTestCase):
    """Sidebar: mehmon — Kirish/Ro'yxatdan o'tish; «Panel» — faqat moderator va undan yuqori."""

    def test_guest_sees_login_and_register(self) -> None:
        response = self.home()
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, f'href="{reverse("register")}"')
        self.assertNotContains(response, f'href="{reverse("panel:home")}"')
        self.assertNotContains(response, f'href="{reverse("my_submissions")}"')

    def test_student_and_jury_do_not_see_panel(self) -> None:
        for role in (Role.USER, Role.JURY, Role.JURY_PRO):
            self.client.force_login(make_user(f"u{role.value}", role))
            response = self.home()
            self.assertContains(response, f'href="{reverse("my_submissions")}"')
            self.assertNotContains(response, f'href="{reverse("panel:home")}"', msg_prefix=role.label)
            self.assertNotContains(response, f'href="{reverse("register")}"')

    def test_moderator_sees_panel(self) -> None:
        self.client.force_login(make_user("moder", Role.MODERATOR))
        self.assertContains(self.home(), f'href="{reverse("panel:home")}"')


class StatsTests(HomeTestCase):
    """Statistika: seed_demo/is_seed akkauntlar va ularning yechimlari, nashr etilmagan vazifalar hisobga olinmaydi."""

    def setUp(self) -> None:
        super().setUp()
        self.problem = Problem.objects.filter(type="code", status=Problem.Status.PUBLISHED).first()

    def submit(self, user: User, verdict: str = Verdict.ACCEPTED) -> None:
        Submission.objects.create(user=user, problem=self.problem, code="x", status=Submission.Status.DONE,
                                  verdict=verdict)

    def test_seed_accounts_and_drafts_excluded(self) -> None:
        base = site_counters()
        cache.clear()
        real = make_user("haqiqiy")
        demo = make_user("demo01", is_seed=True)
        self.submit(real)
        self.submit(real, Verdict.WRONG_ANSWER)
        self.submit(demo)
        self.submit(demo)
        Problem.objects.filter(pk=self.problem.pk).update(status=Problem.Status.DRAFT)
        counters = site_counters()
        self.assertEqual(counters["users"], base["users"] + 1)
        self.assertEqual(counters["submissions"], base["submissions"] + 2)
        self.assertEqual(counters["accepted"], base["accepted"] + 1)
        self.assertEqual(counters["problems"], base["problems"] - 1)

    def test_seed_demo_command_does_not_change_counters(self) -> None:
        base = site_counters()
        cache.clear()
        call_command("seed_demo", students=3, stdout=StringIO())
        self.assertTrue(User.objects.filter(username__startswith="demo", is_seed=True).exists())
        self.assertTrue(Submission.objects.filter(user__is_seed=True).exists())
        self.assertEqual(site_counters(), base)

    def test_counters_cached_for_ten_minutes(self) -> None:
        first = site_counters()
        make_user("yangi")
        self.assertEqual(site_counters(), first)  # kesh
        cache.clear()
        self.assertEqual(site_counters()["users"], first["users"] + 1)

    def test_home_renders_counters_with_plus(self) -> None:
        make_user("talaba")
        response = self.home()
        users = site_counters()["users"]
        self.assertContains(response, f'data-count-to="{users}">{users}+</span>', html=False)
        for label in ("o‘quvchilar", "vazifalar", "yechimlar", "qabul qilingan"):
            self.assertContains(response, label)


class HeroTests(HomeTestCase):
    """Sahifa 200, semantika, CTA havolalari va sayt sozlamalaridagi muallif matnlari."""

    def setUp(self) -> None:
        super().setUp()
        self.course = Course.objects.filter(is_active=True).first()

    def test_page_ok_and_semantics(self) -> None:
        response = self.home()
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('<section class="hero" aria-labelledby="hero-title">', html)
        self.assertIn('id="hero-title"', html)
        self.assertIn("Dasturlashni masala yechib o‘rganing", html)  # breadcrumb
        self.assertIn("O‘quv platformasi", html)
        self.assertIn('alt="Kurs muallifi Nurbek Soliyev"', html)
        self.assertIn('fetchpriority="high"', html)
        self.assertIn("hero-nurbek-800.webp 800w", html)
        self.assertIn("hero-nurbek-1200.webp 1200w", html)
        self.assertEqual(html.count("data-hero-free"), 1)  # «1-dars BEPUL!» — faqat bitta
        self.assertNotIn("icpc", html.lower())
        self.assertNotIn("it park", html.lower())

    def test_guest_cta_links(self) -> None:
        response = self.home()
        self.assertEqual(response.context["hero"], {
            "start": reverse("register"),
            "problems": reverse("problem_list"),
            "lesson1": reverse("lesson_detail", args=[self.course.slug, 1]),
        })
        self.assertContains(response, f'href="{reverse("register")}" data-hero-start')
        self.assertContains(response, f'href="{reverse("problem_list")}" data-hero-problems')
        self.assertContains(response, f'href="{reverse("lesson_detail", args=[self.course.slug, 1])}" data-hero-free')
        self.assertEqual(self.client.get(response.context["hero"]["lesson1"]).status_code, 200)

    def test_guest_cta_when_registration_closed(self) -> None:
        site = SiteSettings.load()
        site.registration_enabled = False
        site.save()
        self.assertEqual(self.home().context["hero"]["start"], reverse("login"))

    def test_logged_in_cta_goes_to_course(self) -> None:
        self.client.force_login(make_user("talaba"))
        response = self.home()
        self.assertContains(response, f'href="{reverse("course_detail", args=[self.course.slug])}" data-hero-start')

    def test_author_card_from_site_settings(self) -> None:
        response = self.home()
        self.assertContains(response, "Kurs muallifi:")
        self.assertContains(response, "Nurbek Soliyev")
        self.assertContains(response, "AI (ML, CV, LLM) va Full-Stack dasturchi")
        site = SiteSettings.load()
        site.hero_author_name = "Boshqa Muallif"
        site.hero_author_title = "Yangi lavozim"
        site.save()
        response = self.home()
        self.assertContains(response, "Boshqa Muallif")
        self.assertContains(response, "Yangi lavozim")
        self.assertContains(response, 'alt="Kurs muallifi Boshqa Muallif"')


class HeroImageTests(TestCase):
    """scripts/make_hero_image.py natijalari repoda mavjud va o'lchamlari to'g'ri."""

    def test_files_exist_with_expected_widths(self) -> None:
        for name, width in (("hero-nurbek-800.webp", 800), ("hero-nurbek-1200.webp", 1200)):
            path = IMG_DIR / name
            self.assertTrue(path.exists(), name)
            with Image.open(path) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.width, width)
        self.assertTrue((IMG_DIR / "hero-nurbek.png").exists())

    def test_template_dimensions_match_800w_image(self) -> None:
        with Image.open(IMG_DIR / "hero-nurbek-800.webp") as image:
            self.assertEqual(image.size, (800, 1042))
