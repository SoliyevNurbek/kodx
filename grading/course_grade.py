"""
Kurs bahosi (musobaqa reytingidan ALOHIDA).

Har modul (standart 20 ball):
- davomat 2,5 — guruhda davomat olingan darslardan qatnashganlari ulushi;
- mustaqil vazifalar 5 — modul darslaridagi majburiy code masalalar bo'yicha o'rtacha natija;
- test 2,5 — modul quiz'lari bo'yicha o'rtacha natija;
- loyiha 10 — modul loyihalari bo'yicha o'rtacha baho.

Har vazifa uchun eng yaxshi natija olinadi; muddatdan keyingi topshiriq bali jarima foiziga kamaytiriladi.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from courses.models import Course, Group, GroupMember, Lesson
from problems.models import LessonProblem, Problem
from submissions.models import ProjectSubmission, QuizAttempt, Submission

from .models import Attendance, GradingPolicy

CENT = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def best_fraction(entries: Iterable[tuple[datetime, float]], deadline: datetime | None, penalty_percent: int) -> float:
    """
    Eng yaxshi natija ulushi (0..1). `entries` — (topshirilgan vaqt, ulush).
    Muddatdan keyingi har bir topshiriq ulushi (100 - jarima)% ga ko'paytiriladi.
    """
    best = 0.0
    factor = (100 - penalty_percent) / 100
    for created_at, fraction in entries:
        value = max(0.0, min(1.0, fraction))
        if deadline is not None and created_at > deadline:
            value *= factor
        best = max(best, value)
    return best


@dataclass
class ModuleGrade:
    number: int
    title: str
    attendance: Decimal = Decimal(0)
    tasks: Decimal = Decimal(0)
    quiz: Decimal = Decimal(0)
    project: Decimal = Decimal(0)
    max_total: Decimal = Decimal(0)

    @property
    def total(self) -> Decimal:
        return self.attendance + self.tasks + self.quiz + self.project


@dataclass
class CourseGrade:
    modules: list[ModuleGrade] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((m.total for m in self.modules), Decimal(0))

    @property
    def max_total(self) -> Decimal:
        return sum((m.max_total for m in self.modules), Decimal(0))


def _entries_for_user(user, problem_ids: set[int]) -> dict[int, list[tuple[datetime, float]]]:
    """{problem_id: [(vaqt, ulush), ...]} — code, quiz va baholangan loyihalar."""
    entries: dict[int, list[tuple[datetime, float]]] = defaultdict(list)
    points = dict(Problem.objects.filter(pk__in=problem_ids).values_list("pk", "points"))
    for problem_id, created, score in Submission.objects.filter(
            user=user, problem_id__in=problem_ids, status=Submission.Status.DONE
    ).values_list("problem_id", "created_at", "score"):
        entries[problem_id].append((created, score / points[problem_id] if points[problem_id] else 0.0))
    for problem_id, created, score, max_score in QuizAttempt.objects.filter(
            user=user, problem_id__in=problem_ids).values_list("problem_id", "created_at", "score", "max_score"):
        entries[problem_id].append((created, score / max_score if max_score else 0.0))
    for problem_id, created, score in ProjectSubmission.objects.filter(
            user=user, problem_id__in=problem_ids, status=ProjectSubmission.Status.GRADED
    ).values_list("problem_id", "created_at", "score"):
        entries[problem_id].append((created, score / points[problem_id] if points[problem_id] else 0.0))
    return entries


def active_group(user, course: Course) -> Group | None:
    membership = GroupMember.objects.filter(user=user, group__course=course, is_active=True).select_related(
        "group").first()
    return membership.group if membership else None


def compute_course_grade(user, course: Course, group: Group | None = None,
                         policy: GradingPolicy | None = None) -> CourseGrade:
    """Foydalanuvchining kurs bahosini modullar bo'yicha hisoblaydi."""
    policy = policy or GradingPolicy.for_course(course)
    group = group or active_group(user, course)
    links = list(LessonProblem.objects.filter(
        lesson__module__course=course, is_required=True, problem__status=Problem.Status.PUBLISHED,
    ).select_related("problem", "lesson__module"))
    entries = _entries_for_user(user, {link.problem_id for link in links})

    attendance_by_module: dict[int, list[bool]] = defaultdict(list)
    if group is not None:
        for module_id, present in Attendance.objects.filter(group=group, user=user).values_list(
                "lesson__module_id", "present"):
            attendance_by_module[module_id].append(present)
        marked_lessons = defaultdict(set)
        for module_id, lesson_id in Attendance.objects.filter(group=group).values_list(
                "lesson__module_id", "lesson_id").distinct():
            marked_lessons[module_id].add(lesson_id)
    else:
        marked_lessons = defaultdict(set)

    fractions: dict[tuple[int, str], list[float]] = defaultdict(list)
    for link in links:
        value = best_fraction(entries.get(link.problem_id, []), link.deadline, policy.late_penalty_percent)
        fractions[(link.lesson.module_id, link.problem.type)].append(value)

    def component(weight: Decimal, values: list[float]) -> Decimal:
        if not values:
            return Decimal(0)
        return _q(weight * Decimal(str(sum(values) / len(values))))

    result = CourseGrade()
    for module in course.modules.order_by("number"):
        grade = ModuleGrade(number=module.number, title=module.title, max_total=policy.module_total)
        marked = len(marked_lessons[module.pk])
        if marked:
            present = sum(attendance_by_module[module.pk])
            grade.attendance = _q(policy.attendance_points * Decimal(present) / Decimal(marked))
        grade.tasks = component(policy.tasks_points, fractions[(module.pk, Problem.Type.CODE)])
        grade.quiz = component(policy.quiz_points, fractions[(module.pk, Problem.Type.QUIZ)])
        grade.project = component(policy.project_points, fractions[(module.pk, Problem.Type.PROJECT)])
        result.modules.append(grade)
    return result


def group_grades(group: Group) -> list[tuple[object, CourseGrade]]:
    """Guruhdagi faol o'quvchilarning baholari."""
    policy = GradingPolicy.for_course(group.course)
    members = group.members.filter(is_active=True).select_related("user").order_by("user__username")
    return [(m.user, compute_course_grade(m.user, group.course, group, policy)) for m in members]


def lessons_of(course: Course) -> list[Lesson]:
    return list(Lesson.objects.filter(module__course=course).order_by("number"))
