"""Rol panellari URL'lari."""

from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.home, name="home"),
    # O'qituvchi
    path("guruhlar/", views.groups, name="groups"),
    path("guruhlar/<int:pk>/", views.group_progress, name="group_progress"),
    path("yechimlar/", views.submissions_feed, name="submissions"),
    path("loyihalar/", views.projects_queue, name="projects"),
    path("loyihalar/<int:pk>/", views.project_grade, name="project_grade"),
    path("rol-sorovlari/", views.role_requests, name="role_requests"),
    path("foydalanuvchilar/", views.users, name="users"),
    # Jury Pro
    path("vazifalarim/", views.my_problems, name="my_problems"),
    path("vazifalarim/yangi/", views.problem_create, name="problem_create"),
    path("vazifalarim/<slug:slug>/", views.problem_edit, name="problem_edit"),
    path("vazifalarim/<slug:slug>/testlar/", views.problem_tests, name="problem_tests"),
    path("vazifalarim/<slug:slug>/testlar/<int:pk>/ochirish/", views.test_delete, name="test_delete"),
    path("vazifalarim/<slug:slug>/tekshirish/", views.problem_check, name="problem_check"),
    path("vazifalarim/<slug:slug>/korib-chiqishga/", views.problem_submit_review, name="problem_submit_review"),
    # Super admin
    path("tizim/", views.system, name="system"),
    path("audit/", views.audit_log, name="audit"),
]
