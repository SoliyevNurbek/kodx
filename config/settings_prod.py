"""
Production sozlamalari: `DJANGO_SETTINGS_MODULE=config.settings_prod`.

Asosiy sozlamalarni meros qilib oladi va xavfsizlikni kuchaytiradi. Tekshirish:
    python manage.py check --deploy --settings=config.settings_prod
"""

from .settings import *  # noqa: F403
from .settings import env, env_list

DEBUG = False
ALLOWED_HOSTS = env_list("PROD_ALLOWED_HOSTS", "kodx.uz,www.kodx.uz")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

# HTTPS (nginx orqasida — X-Forwarded-Proto ga ishonamiz)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie'lar faqat HTTPS orqali, JavaScript'dan yashirin
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

# Content-Security-Policy va boshqa sarlavhalar (core.middleware)
CSP_ENABLED = True
KODX_REQUIRE_SUPERADMIN_2FA = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Kod faqat Judge0 da (LocalDevBackend DEBUG=False da o'zi ham ishlamaydi)
JUDGE_BACKEND = "judge0"

# Email: haqiqiy SMTP (.env: EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
