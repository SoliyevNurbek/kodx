"""
Rol panellari.

- O'qituvchi (moderator+): guruhlar va progress, yechimlar oqimi, loyihalarni baholash, rol so'rovlari, rollar.
- Jury Pro: o'z vazifalari — yaratish, tahrirlash, testlar, etalon yechim bilan tekshirish, ko'rib chiqishga yuborish.
- Super admin: tizim sozlamalari, audit jurnali, tizim holati.
"""

import csv
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Role, RoleRequest, User
from accounts.permissions import role_required
from audit.models import AuditLog
from audit.services import log_action
from core.models import SiteSettings
from courses.models import Group, Lesson
from grading.course_grade import group_grades as group_grades_for
from grading.models import Attendance
from problems.models import LessonProblem, Problem, TestCase
from submissions.models import ProjectSubmission, Submission
from submissions.queue import get_queue
from submissions.services import SubmissionError, create_submission, grade_project
from submissions.stats import solved_map

from .forms import GradeForm, ProblemForm, SiteSettingsForm, TestUploadForm


@role_required(Role.JURY)
def home(request: HttpRequest) -> HttpResponse:
    context = {}
    if request.user.is_moderator:
        context["pending_projects"] = ProjectSubmission.objects.filter(
            status=ProjectSubmission.Status.SUBMITTED).count()
        context["pending_roles"] = RoleRequest.objects.filter(status=RoleRequest.Status.PENDING).count()
    if request.user.is_jury_pro:
        context["my_problems"] = Problem.objects.filter(author=request.user).count()
    return render(request, "panel/home.html", context)


# ---------------- O'qituvchi (moderator) ----------------

@role_required(Role.MODERATOR)
def groups(request: HttpRequest) -> HttpResponse:
    items = Group.objects.select_related("course", "teacher").order_by("-is_active", "name")
    return render(request, "panel/groups.html", {"groups": items})


@role_required(Role.MODERATOR)
def group_progress(request: HttpRequest, pk: int) -> HttpResponse:
    """Progress jadvali: o'quvchi × dars (majburiy vazifalardan nechtasi yechilgan)."""
    group = get_object_or_404(Group.objects.select_related("course"), pk=pk)
    members = list(group.members.filter(is_active=True).select_related("user").order_by("user__username"))
    lessons = list(Lesson.objects.filter(module__course=group.course).order_by("number"))
    required: dict[int, set[int]] = {lesson.pk: set() for lesson in lessons}
    for lesson_id, problem_id in LessonProblem.objects.filter(
            lesson__in=lessons, is_required=True, problem__status=Problem.Status.PUBLISHED
    ).values_list("lesson_id", "problem_id"):
        required[lesson_id].add(problem_id)
    solved = solved_map([m.user_id for m in members])
    rows = []
    for member in members:
        done = solved.get(member.user_id, set())
        cells = []
        for lesson in lessons:
            total = len(required[lesson.pk])
            got = len(required[lesson.pk] & done)
            cells.append({"lesson": lesson, "done": got, "total": total,
                          "level": 0 if not total or not got else 3 if got == total else 1 if got * 2 < total else 2})
        rows.append({"user": member.user, "cells": cells, "total": sum(c["done"] for c in cells)})
    return render(request, "panel/group_progress.html", {"group": group, "lessons": lessons, "rows": rows})


@role_required(Role.MODERATOR)
def submissions_feed(request: HttpRequest) -> HttpResponse:
    items = Submission.objects.select_related("user", "problem")
    group_id = request.GET.get("group", "")
    if group_id.isdigit():
        items = items.filter(user__group_memberships__group_id=int(group_id))
    page = Paginator(items, 50).get_page(request.GET.get("page"))
    return render(request, "panel/submissions.html",
                  {"page": page, "groups": Group.objects.filter(is_active=True), "group_id": group_id})


@role_required(Role.MODERATOR)
def projects_queue(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", ProjectSubmission.Status.SUBMITTED)
    items = ProjectSubmission.objects.select_related("user", "problem")
    if status in ProjectSubmission.Status.values:
        items = items.filter(status=status)
    page = Paginator(items.order_by("created_at"), 30).get_page(request.GET.get("page"))
    return render(request, "panel/projects.html",
                  {"page": page, "status": status, "statuses": ProjectSubmission.Status.choices})


@role_required(Role.MODERATOR)
def project_grade(request: HttpRequest, pk: int) -> HttpResponse:
    submission = get_object_or_404(ProjectSubmission.objects.select_related("user", "problem"), pk=pk)
    rubric = submission.problem.rubric.all()
    initial = {f"c{k}": v for k, v in submission.rubric_scores.items()} | {"feedback": submission.feedback}
    form = GradeForm(request.POST or None, rubric=rubric, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            grade_project(request.user, submission, form.scores(), form.cleaned_data["feedback"],
                          needs_revision=form.cleaned_data["needs_revision"], request=request)
        except (SubmissionError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Baholandi: {submission.score} ball.")
            return redirect("panel:projects")
    history = ProjectSubmission.objects.filter(user=submission.user, problem=submission.problem).exclude(pk=pk)
    return render(request, "panel/project_grade.html", {"submission": submission, "form": form, "history": history})


@role_required(Role.MODERATOR)
def role_requests(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        role_request = get_object_or_404(RoleRequest, pk=request.POST.get("request_id"))
        try:
            if request.POST.get("decision") == "approve":
                role_request.approve(request.user, request.POST.get("comment", ""), request=request)
            else:
                role_request.reject(request.user, request.POST.get("comment", ""), request=request)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [str(exc)])))
        else:
            messages.success(request, "So‘rov ko‘rib chiqildi.")
        return redirect("panel:role_requests")
    pending = RoleRequest.objects.filter(status=RoleRequest.Status.PENDING).select_related("user")
    recent = RoleRequest.objects.exclude(status=RoleRequest.Status.PENDING).select_related("user", "reviewed_by")[:20]
    return render(request, "panel/role_requests.html", {"pending": pending, "recent": recent})


@role_required(Role.MODERATOR)
def users(request: HttpRequest) -> HttpResponse:
    """Foydalanuvchilar va rol berish (moderator — jury/jury_pro, super admin — barchasi)."""
    if request.method == "POST":
        target = get_object_or_404(User, pk=request.POST.get("user_id"))
        try:
            new_role = int(request.POST.get("role", ""))
        except ValueError:
            new_role = -1
        actor = request.user
        allowed = (new_role in Role.values and actor.can_assign_role(new_role) and target.pk != actor.pk
                   and (actor.is_superadmin or target.role_level < actor.role_level))
        if not allowed:
            raise PermissionDenied("Bu rolni berishga huquqingiz yo‘q.")
        old_role = target.role
        target.role = new_role
        target.save(update_fields=["role"])
        log_action(actor, "user_role_changed", target, {"old": old_role, "new": new_role}, request)
        messages.success(request, f"{target.username}: {target.get_role_display()}")
        return redirect(f"{request.path}?q={target.username}")
    query = request.GET.get("q", "").strip()
    items = User.objects.filter(is_active=True).order_by("username")
    if query:
        items = items.filter(Q(username__icontains=query) | Q(first_name__icontains=query)
                             | Q(last_name__icontains=query))
    page = Paginator(items, 30).get_page(request.GET.get("page"))
    roles = [(v, label) for v, label in Role.choices if request.user.can_assign_role(v)]
    return render(request, "panel/users.html", {"page": page, "query": query, "roles": roles})


# ---------------- Jury Pro: o'z vazifalari ----------------

def _own_problem(request: HttpRequest, slug: str) -> Problem:
    problem = get_object_or_404(Problem, slug=slug)
    if not problem.can_edit(request.user):
        raise PermissionDenied("Faqat o‘z vazifangizni tahrirlay olasiz.")
    return problem


@role_required(Role.JURY_PRO)
def my_problems(request: HttpRequest) -> HttpResponse:
    items = Problem.objects.filter(author=request.user).order_by("-updated_at")
    return render(request, "panel/my_problems.html", {"problems": items})


@role_required(Role.JURY_PRO)
def problem_create(request: HttpRequest) -> HttpResponse:
    form = ProblemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        problem = form.save(commit=False)
        problem.author = request.user
        problem.status = Problem.Status.DRAFT
        problem.save()
        form.save_m2m()
        log_action(request.user, "problem_created", problem, request=request)
        messages.success(request, "Vazifa yaratildi. Endi testlarni yuklang.")
        return redirect("panel:problem_tests", slug=problem.slug)
    return render(request, "panel/problem_form.html", {"form": form, "problem": None})


@role_required(Role.JURY_PRO)
def problem_edit(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _own_problem(request, slug)
    form = ProblemForm(request.POST or None, instance=problem)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request.user, "problem_updated", problem, {"changed": form.changed_data}, request)
        messages.success(request, "Saqlandi.")
        return redirect("panel:problem_edit", slug=slug)
    return render(request, "panel/problem_form.html", {"form": form, "problem": problem})


@role_required(Role.JURY_PRO)
def problem_tests(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _own_problem(request, slug)
    form = TestUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        order = (problem.test_cases.order_by("-order").values_list("order", flat=True).first() or 0) + 1
        test = TestCase(problem=problem, order=order, is_sample=form.cleaned_data["is_sample"],
                        points=form.cleaned_data["points"])
        test.input_file.save(f"{order:02d}.in", form.cleaned_data["input_file"], save=False)
        test.output_file.save(f"{order:02d}.out", form.cleaned_data["output_file"], save=False)
        test.save()
        log_action(request.user, "test_added", problem, {"order": order}, request)
        messages.success(request, f"Test #{order} qo‘shildi.")
        return redirect("panel:problem_tests", slug=slug)
    return render(request, "panel/problem_tests.html",
                  {"problem": problem, "form": form, "tests": problem.test_cases.all()})


@role_required(Role.JURY_PRO)
@require_POST
def test_delete(request: HttpRequest, slug: str, pk: int) -> HttpResponse:
    problem = _own_problem(request, slug)
    test = get_object_or_404(TestCase, pk=pk, problem=problem)
    log_action(request.user, "test_deleted", problem, {"order": test.order}, request)
    test.delete()
    messages.success(request, "Test o‘chirildi.")
    return redirect("panel:problem_tests", slug=slug)


@role_required(Role.JURY_PRO)
@require_POST
def problem_check(request: HttpRequest, slug: str) -> HttpResponse:
    """Etalon yechimni navbat orqali (worker'da) tekshirish — web jarayonda kod bajarilmaydi."""
    problem = _own_problem(request, slug)
    if problem.type != Problem.Type.CODE:
        raise Http404
    try:
        submission = create_submission(request.user, problem, problem.reference_solution)
    except SubmissionError as exc:
        messages.error(request, exc.messages[0])
        return redirect("panel:problem_tests", slug=slug)
    return redirect("submission_detail", pk=submission.pk)


@role_required(Role.JURY_PRO)
@require_POST
def problem_submit_review(request: HttpRequest, slug: str) -> HttpResponse:
    problem = _own_problem(request, slug)
    if problem.status != Problem.Status.DRAFT:
        messages.error(request, "Faqat qoralamani ko‘rib chiqishga yuborish mumkin.")
    elif problem.type == Problem.Type.CODE and not problem.test_cases.exists():
        messages.error(request, "Avval testlarni yuklang.")
    else:
        problem.status = Problem.Status.REVIEW
        problem.save(update_fields=["status", "updated_at"])
        log_action(request.user, "problem_sent_to_review", problem, request=request)
        messages.success(request, "Vazifa moderatorga ko‘rib chiqish uchun yuborildi.")
    return redirect("panel:my_problems")


# ---------------- Super admin ----------------

@role_required(Role.SUPERADMIN)
def system(request: HttpRequest) -> HttpResponse:
    settings_obj = SiteSettings.load()
    form = SiteSettingsForm(request.POST or None, instance=settings_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request.user, "site_settings_updated", settings_obj, {"changed": form.changed_data}, request)
        messages.success(request, "Sozlamalar saqlandi.")
        return redirect("panel:system")
    last_judged = Submission.objects.exclude(judged_at=None).order_by("-judged_at").values_list(
        "judged_at", flat=True).first()
    queue_size = get_queue().size()
    worker_ok = queue_size == 0 or bool(last_judged and timezone.now() - last_judged < timedelta(minutes=2))
    status = {
        "queue_size": queue_size,
        "running": Submission.objects.filter(status=Submission.Status.RUNNING).count(),
        "last_judged": last_judged,
        "worker_ok": worker_ok,
        "users": User.objects.count(),
        "submissions_today": Submission.objects.filter(created_at__gte=timezone.now() - timedelta(days=1)).count(),
    }
    return render(request, "panel/system.html", {"form": form, "status": status})


@role_required(Role.SUPERADMIN)
def audit_log(request: HttpRequest) -> HttpResponse:
    items = AuditLog.objects.select_related("actor")
    action, actor = request.GET.get("action", ""), request.GET.get("actor", "")
    if action:
        items = items.filter(action=action)
    if actor:
        items = items.filter(actor__username=actor)
    page = Paginator(items, 50).get_page(request.GET.get("page"))
    actions = AuditLog.objects.order_by("action").values_list("action", flat=True).distinct()
    return render(request, "panel/audit.html", {"page": page, "actions": actions, "action": action, "actor": actor})


# ---------------- Baholash: kurs baholari va davomat ----------------

@role_required(Role.MODERATOR)
def group_grades(request: HttpRequest, pk: int) -> HttpResponse:
    """Guruh baholari jadvali; ?format=csv — CSV eksport."""
    group = get_object_or_404(Group.objects.select_related("course"), pk=pk)
    grades = group_grades_for(group)
    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="baholar-{group.pk}.csv"'
        response.write("﻿")  # Excel UTF-8 ni to'g'ri ochishi uchun BOM
        writer = csv.writer(response)
        modules = grades[0][1].modules if grades else []
        header = ["username", "ism"]
        for module in modules:
            header += [f"M{module.number} davomat", f"M{module.number} vazifalar", f"M{module.number} test",
                       f"M{module.number} loyiha", f"M{module.number} jami"]
        writer.writerow(header + ["jami"])
        for user, grade in grades:
            row = [user.username, user.get_full_name()]
            for module in grade.modules:
                row += [module.attendance, module.tasks, module.quiz, module.project, module.total]
            writer.writerow(row + [grade.total])
        log_action(request.user, "grades_exported", group, request=request)
        return response
    return render(request, "panel/group_grades.html", {"group": group, "grades": grades})


@role_required(Role.MODERATOR)
def group_attendance(request: HttpRequest, pk: int) -> HttpResponse:
    """Dars bo'yicha davomatni belgilash."""
    group = get_object_or_404(Group.objects.select_related("course"), pk=pk)
    lessons = Lesson.objects.filter(module__course=group.course).order_by("number")
    number = request.POST.get("lesson") or request.GET.get("lesson") or "1"
    lesson = get_object_or_404(lessons, number=int(number) if str(number).isdigit() else 1)
    members = list(group.members.filter(is_active=True).select_related("user").order_by("user__username"))
    if request.method == "POST":
        present_ids = {int(v) for v in request.POST.getlist("present") if v.isdigit()}
        for member in members:
            Attendance.objects.update_or_create(
                group=group, lesson=lesson, user=member.user,
                defaults={"present": member.user_id in present_ids, "marked_by": request.user})
        log_action(request.user, "attendance_marked", group,
                   {"lesson": lesson.number, "present": len(present_ids), "total": len(members)}, request)
        messages.success(request, f"{lesson.number}-dars davomati saqlandi.")
        return redirect(f"{request.path}?lesson={lesson.number}")
    marked = dict(Attendance.objects.filter(group=group, lesson=lesson).values_list("user_id", "present"))
    rows = [{"user": m.user, "present": marked.get(m.user_id, True), "marked": m.user_id in marked} for m in members]
    return render(request, "panel/group_attendance.html",
                  {"group": group, "lesson": lesson, "lessons": lessons, "rows": rows})
