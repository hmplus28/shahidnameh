"""تنظیمات اصلی پلتفرم یادبود شهیدنامه."""
from pathlib import Path
import os
import sys

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# لودر فایل ‎.env‎ — مخصوص استقرار روی cPanel/Passenger
#
# Passenger فایل ‎.env‎ را خودکار نمی‌خواند؛ بنابراین مقادیر محیطی (کلید امنیتی،
# DEBUG، دیتابیس و…) از این فایل خوانده می‌شوند. متغیرهای واقعی محیط همیشه
# اولویت دارند (setdefault) و اگر ‎.env‎ وجود نداشته باشد چیزی خراب نمی‌شود.
# ─────────────────────────────────────────────────────────────────────────────
def _load_dotenv(path: Path) -> None:
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "development-only-change-this-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        # دامنه‌های موقت تانل Cloudflare برای ورود پنل از اینترنت
        "https://genre-jurisdiction-demonstrate-lights.trycloudflare.com,"
        "https://photographers-beth-jury-stainless.trycloudflare.com,"
        "https://velocity-funny-automation-twice.trycloudflare.com,"
    ).split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "whitenoise.runserver_nostatic",
    "jalali_date",
    "martyrs.apps.MartyrsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "config.middleware.NoCacheHTMLMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

X_FRAME_OPTIONS = "ALLOWALL"
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
                "config.context_processors.site_settings",
                "config.context_processors.background_assets",
                "config.context_processors.site_elements",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─────────────────────────────────────────────────────────────────────────────
# دیتابیس — فقط MySQL/MariaDB
#
# این پروژه الزاماً با MySQL/MariaDB کار می‌کند (پیش‌فرض هاست‌های cPanel).
# مشخصات از فایل ‎.env‎ خوانده می‌شود:
#   DB_NAME / DB_USER / DB_PASSWORD  (الزامی)
#   DB_HOST (پیش‌فرض localhost) / DB_PORT (پیش‌فرض 3306)
# روی cPanel نام دیتابیس و یوزر معمولاً به‌شکل ‎<یوزر-سی‌پنل>_shahidnameh‎ است.
# راهنمای ساخت دیتابیس: deploy/GUIDE-CPANEL-FA.md
# ─────────────────────────────────────────────────────────────────────────────
_DATABASE_NAME = os.environ.get("DB_NAME", "").strip()
_DATABASE_USER = os.environ.get("DB_USER", "").strip()

if not _DATABASE_NAME or not _DATABASE_USER:
    raise ImproperlyConfigured(
        "این پروژه فقط با MySQL/MariaDB کار می‌کند و DB_NAME/DB_USER در فایل .env تنظیم نشده است.\n"
        "در cPanel بخش «MySQL® Databases» یک دیتابیس و یوزر بسازید و در .env بنویسید:\n"
        "  DB_NAME=<یوزر-سی‌پنل>_shahidnameh\n"
        "  DB_USER=<یوزر-سی‌پنل>_shahidnameh\n"
        "  DB_PASSWORD=رمز-دیتابیس\n"
        "راهنمای کامل: deploy/GUIDE-CPANEL-FA.md"
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": _DATABASE_NAME,
        "USER": _DATABASE_USER,
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        # اتصال پایدار در Passenger (اتصال دوباره پس از ۶۰ ثانیه بیکاری)
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "charset": "utf8mb4",
            # برای پشتیبانی کامل از متن فارسی و ایموجی
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        # دیتابیس تست هم الزاماً utf8mb4 ساخته شود (بعضی سرورها پیش‌فرض latin1
        # دارند و متن فارسی در تست‌ها خطای Incorrect string value می‌دهد)
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa"
LANGUAGES = [("fa", "فارسی")]
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# در حالت اجرای تست‌ها، استوریج manifest whitenoise بدون اجرای قبلیِ
# collectstatic خطای «Missing staticfiles manifest entry» می‌دهد و تست‌ها
# از یک کلون تازه قابل اجرا نیستند؛ در تست‌ها از استوریج ساده استفاده می‌کنیم.
# (در تولید manifest لازم است و deploy/deploy_cpanel.sh خودش collectstatic
# را اجرا می‌کند.)
if "test" in sys.argv:
    STORAGES = {
        **STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# تنظیمات نمایش و انتخاب تاریخ در تقویم جلالی برای فرم‌ها و پنل مدیریت.
JALALI_DATE_DEFAULTS = {
    "LIST_DISPLAY_AUTO_CONVERT": True,
    "Strftime": {
        "date": "%Y/%m/%d",
        "datetime": "%H:%M:%S | %Y/%m/%d",
    },
    "Static": {
        "js": ["admin/js/django_jalali.min.js"],
        "css": {"all": ["admin/css/django_jalali.min.css"]},
    },
}

# کوکی‌ها و حفاظت پیش‌فرض برای بخش مدیریت.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "ALLOWALL"
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
