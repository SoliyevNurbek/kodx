"""kodx.uz — asosiy URL marshrutlari."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import views as account_views
from contests import views as contest_views
from core import views as core_views
from courses import views as course_views
from problems import views as problem_views
from submissions import views as submission_views

admin.site.site_header = "kodx.uz boshqaruv paneli"
admin.site.site_title = "kodx.uz"
admin.site.index_title = "Boshqaruv"

urlpatterns = [
    path("", core_views.home, name="home"),
    path("reyting/", core_views.leaderboard, name="leaderboard"),
    # Hisob
    path("accounts/register/", account_views.register, name="register"),
    path("accounts/password_change/", account_views.KodxPasswordChangeView.as_view(), name="password_change"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sozlamalar/profil/", account_views.profile_edit, name="profile_edit"),
    path("u/<str:username>/", account_views.profile, name="profile"),
    # Kurs
    path("kurs/<slug:slug>/", course_views.course_detail, name="course_detail"),
    path("kurs/<slug:slug>/dars/<int:number>/", course_views.lesson_detail, name="lesson_detail"),
    # Vazifalar
    path("masalalar/", problem_views.problem_list, name="problem_list"),
    path("masalalar/<slug:slug>/", problem_views.problem_detail, name="problem_detail"),
    path("masalalar/<slug:slug>/yuborish/", problem_views.submit_code, name="submit_code"),
    path("masalalar/<slug:slug>/quiz/", problem_views.submit_quiz, name="submit_quiz"),
    path("masalalar/<slug:slug>/loyiha/", problem_views.submit_project_view, name="submit_project"),
    path("quiz/<int:pk>/", problem_views.quiz_result, name="quiz_result"),
    # Urinishlar
    path("urinishlar/", submission_views.my_submissions, name="my_submissions"),
    path("urinishlar/<int:pk>/", submission_views.submission_detail, name="submission_detail"),
    path("urinishlar/<int:pk>/holat/", submission_views.submission_status, name="submission_status"),
    # Kontestlar
    path("kontestlar/", contest_views.contest_list, name="contest_list"),
    # Panellar va admin
    path("panel/", include("panel.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
