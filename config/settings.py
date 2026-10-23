"""
kodx.uz — Django sozlamalari.

Barcha maxfiy va muhitga bog'liq qiymatlar .env faylidan o'qiladi
(namuna: .env.example).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str | None = None) -> str:
    """.env dan qiymat oladi; majburiy qiymat yo'q bo'lsa xato beradi."""
    value = os.getenv(name, default)
    if value is None:
        raise ImproperlyConfigured(f".env da {name} sozlanmagan")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    """.env dagi qiymatni bool ga aylantiradi."""
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Vergul bilan ajratilgan qiymatni ro'yxatga aylantiradi."""
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("SECRET_KEY")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost")


# Ilovalar

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Loyiha ilovalari
    "accounts",
    "audit",
    "courses",
    "problems",
    "submissions",
    "contests",
    "judge",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Ma'lumotlar bazasi — MySQL 8, utf8mb4

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": "test_" + env("DB_NAME"),
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}


# Autentifikatsiya

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Til va vaqt

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True


# Statik va media fayllar

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Testlar: vaqtinchalik MEDIA_ROOT va TESTING belgisi (config/test_runner.py)

TEST_RUNNER = "config.test_runner.KodxTestRunner"
TESTING = False


# Judge (kodni tekshirish). "local" — faqat DEBUG uchun, production'da "judge0".

JUDGE_BACKEND = env("JUDGE_BACKEND", "local" if DEBUG else "judge0")
JUDGE0_URL = env("JUDGE0_URL", "")
JUDGE0_TOKEN = env("JUDGE0_TOKEN", "")
JUDGE0_AUTH_HEADER = env("JUDGE0_AUTH_HEADER", "X-Auth-Token")
# Navbat: hozir MySQL; keyin Redis/Celery klassi bilan almashtiriladi (submissions.queue.JudgeQueue)
JUDGE_QUEUE = env("JUDGE_QUEUE", "submissions.queue.DatabaseQueue")
