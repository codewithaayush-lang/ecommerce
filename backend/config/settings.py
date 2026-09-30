"""
Django settings for the e-commerce backend.

All configuration is read from the environment and validated at start-up by
`config.env`. A misconfigured deployment raises ImproperlyConfigured and
refuses to boot rather than running insecurely.

`config.env` adapts a few defaults when it detects a serverless host such as
Vercel (deployment hostnames, no connection reuse). The same settings work
unchanged on a long-lived host like Render.

See `.env.example` for the supported variables.
"""

from config.env import (  # noqa: F401  (re-exported for Django/DRF settings)
    ALLOWED_HOSTS,
    CSRF_COOKIE_SAMESITE,
    CSRF_COOKIE_SECURE,
    CSRF_TRUSTED_ORIGINS,
    DEBUG,
    LOG_FORMAT,
    LOG_LEVEL,
    POSTGRES_CONN_MAX_AGE,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_SSLMODE,
    POSTGRES_USER,
    SECRET_KEY,
    SECURE_CONTENT_TYPE_NOSNIFF,
    SECURE_HSTS_INCLUDE_SUBDOMAINS,
    SECURE_HSTS_PRELOAD,
    SECURE_HSTS_SECONDS,
    SECURE_PROXY_SSL_HEADER,
    SECURE_REFERRER_POLICY,
    SECURE_SSL_REDIRECT,
    SESSION_COOKIE_AGE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    SESSION_ENGINE,
    SESSION_EXPIRE_AT_BROWSER_CLOSE,
    TESTING,
    USE_X_FORWARDED_HOST,
    X_FRAME_OPTIONS,
)
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Build paths inside the project like this: BASE_DIR / "subdir".

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "products",
    "accounts",
    "cart",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [],
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
# ASGI_APPLICATION is intentionally not set. This project is entirely
# synchronous, and a host that auto-detects an entrypoint (Vercel does) prefers
# ASGI whenever it is defined, which would silently run the app under a
# different server than the one used elsewhere. Declaring WSGI only keeps a
# single, well-defined deployment target.
# ASGI_APPLICATION = "config.asgi.application"


# Database
#
# PostgreSQL only. There is no SQLite fallback: the engine is fixed, so a
# misconfigured environment fails instead of silently creating a local file.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        # Fail fast if PostgreSQL is unreachable instead of hanging a request.
        "CONN_MAX_AGE": POSTGRES_CONN_MAX_AGE,
        "OPTIONS": {
            "connect_timeout": 5,
            # TLS to a managed database; omitted when the variable is unset.
            **({"sslmode": POSTGRES_SSLMODE} if POSTGRES_SSLMODE else {}),
        },
        "ATOMIC_REQUESTS": False,
    }
}

# During tests Django builds and tears down its own test database.
if TESTING:
    DATABASES["default"]["NAME"] = POSTGRES_DB


# Django REST Framework
#
# Session authentication. `SessionAuthentication` also runs Django's CSRF check
# on unsafe methods, so authenticated writes are CSRF-protected without any
# custom token handling.
#
# Permissions default to AllowAny so the public catalog stays open; the cart and
# order views opt in with `IsAuthenticated` explicitly.

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "config.authentication.SessionAuthenticationWith401",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    # Never let an unexpected exception leak a stack trace or settings in the
    # response body; log it server-side instead.
    "EXCEPTION_HANDLER": "config.errors.api_exception_handler",
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files
#
# STATIC_URL is absolute so it resolves correctly from any route depth. Static
# files are collected into STATIC_ROOT by `manage.py collectstatic` during the
# build step; this service serves the API and does not serve them at runtime.

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []


# Logging
#
# Structured to stdout so a PaaS log drain captures it. Third-party loggers are
# pinned to WARNING to keep request logs readable.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": LOG_FORMAT},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.db.backends": {
            # SQL echoes are noisy and can contain customer data.
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "rest_framework": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "security": {
            # Django's own security warnings (W004, W009, ...) must always show.
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
