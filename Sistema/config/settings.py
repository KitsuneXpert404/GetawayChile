"""
Django settings for Getaway Chile ERP.
"""
import os
from pathlib import Path
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file automatically (for local development)
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-change-in-production")
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
_hosts = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com")
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]

# HTTPS / CSRF (required on Render)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

# ===================================================================
# SECURITY — only active in production (DEBUG=False)
# ===================================================================
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_BROWSER_XSS_FILTER = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "widget_tweaks",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "users",
    "catalog",
    "clients",
    "sales",
    "logistics",
    "core", # Core App for Frontend
    "notifications",
    "tickets",
    "simple_history",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.ActiveUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.config(default=os.environ.get("DATABASE_URL"), conn_max_age=600)}
elif os.environ.get("USE_POSTGRES", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("PG_DATABASE", "getaway_chile"),
            "USER": os.environ.get("PG_USER", "postgres"),
            "PASSWORD": os.environ.get("PG_PASSWORD", "postgres"),
            "HOST": os.environ.get("PG_HOST", "localhost"),
            "PORT": os.environ.get("PG_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "users.CustomUser"

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cloudinary for persistent media on Render (set CLOUDINARY_URL env var)
if os.environ.get("CLOUDINARY_URL"):
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication", # Process Session Auth for Templates
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

_cors = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]

LOGIN_REDIRECT_URL = "home"  # → goes to splash screen first, then dashboard
LOGOUT_REDIRECT_URL = "home"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"], # Add templates directory
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.notifications_processor",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    # Custom Validator for Uppercase (Can be done here or in a utils file, but for simplicity relying on regex in frontend + custom clean in form is easier for now, 
    # but let's stick to standard validators for backend enforcement. 
    # Adding a simple help text or custom validator class would be ideal, 
    # but user asked for "minimum 8 chars", "uppercase", "numbers".
]

# Auth redirections
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'  # Auto-redirects to role specifics
LOGOUT_REDIRECT_URL = 'public_home'

# Dominio público (opcional). Para enlaces en correos; en Render suele bastar la URL del servicio.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "").strip()

# ===================================================================
# EMAIL — SMTP (Google Workspace / Zoho / otro)
# En producción (DEBUG=False) se usa SMTP; en dev puede ser console.
# Configura en Render: EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
# ===================================================================
if not DEBUG:
    # Producción: forzar backend SMTP para que los correos se envíen de verdad
    _email_backend = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
else:
    # En local también usamos SMTP o el que esté configurado
    _email_backend = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

if os.environ.get("BREVO_API_KEY"):
    EMAIL_BACKEND = "core.brevo_backend.BrevoAPIBackend"
else:
    EMAIL_BACKEND = _email_backend
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
_default_from = os.environ.get("DEFAULT_FROM_EMAIL", "").strip()
DEFAULT_FROM_EMAIL = _default_from or EMAIL_HOST_USER or "noreply@getawaychile.cl"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ===================================================================
# TWILIO — WhatsApp notifications
# ===================================================================
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
