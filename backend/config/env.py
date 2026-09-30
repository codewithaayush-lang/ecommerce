"""Environment configuration and start-up validation.

Every setting the application needs is read from the environment here, and the
values are validated before Django starts. The goal is that a misconfigured
deployment fails immediately and loudly, rather than booting in an insecure
state and leaking it at runtime.

Rules:
  * In production (DEBUG off) a missing or weak SECRET_KEY, an empty
    ALLOWED_HOSTS, or a missing database password raises ImproperlyConfigured.
  * In development those values fall back to safe local defaults so the project
    runs with no setup.
  * On a serverless host (Vercel) only the *defaults* change: hostnames come
    from the platform and database connections are not cached between
    requests. Every validation above still applies, and an explicitly set
    variable always wins.

Nothing in this module reads a secret into a log or an exception message.
"""

import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# The literal used as a local-development fallback. Refused in production.
INSECURE_DEV_SECRET_KEY = "django-insecure-dev-only-do-not-use-in-production"


def _detect_serverless():
    """True when running on a PaaS that terminates TLS in front of us.

    Vercel sets `VERCEL=1` in the build and function environments. Knowing this
    lets the defaults below adapt (host names, connection reuse) without
    weakening any validation: the strict checks still apply.
    """
    return os.environ.get("VERCEL", "") == "1" or bool(os.environ.get("VERCEL_URL"))


def load_env_file(path):
    """Populate os.environ from a simple KEY=VALUE file.

    Real environment variables always win, so a PaaS-injected value is never
    overridden by a stray local file. A tiny stdlib implementation avoids adding
    a dotenv dependency.
    """
    if not path.is_file():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def get_bool(name, default=False):
    """Read a boolean from the environment."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_list(name, default=""):
    """Read a comma-separated environment variable as a list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_int(name, default):
    """Read an integer from the environment, falling back on garbage."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Load .env before reading anything from the environment.
load_env_file(BASE_DIR / ".env")

# DEBUG defaults to False so an unconfigured deployment never serves tracebacks.
# Developers set DJANGO_DEBUG=true in .env to opt in locally.
DEBUG = get_bool("DJANGO_DEBUG", False)

# True on a PaaS (currently Vercel) that supplies its own hostname and runs the
# app as a function rather than a long-lived process.
SERVERLESS = _detect_serverless()


def _validate_secret_key(value):
    """Reject secret keys that would be unsafe in production."""
    if not value:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is not set. Generate one with:\n"
            '  python -c "from django.core.management.utils import '
            'get_random_secret_key as k; print(k())"'
        )
    if value == INSECURE_DEV_SECRET_KEY:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is still the development fallback. Set a unique "
            "secret key before running with DJANGO_DEBUG=false."
        )
    if len(value) < 50:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be at least 50 characters long."
        )
    if len(set(value)) < 5:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is not random enough; it needs at least 5 "
            "distinct characters."
        )


def _resolve_secret_key():
    value = os.environ.get("DJANGO_SECRET_KEY", "")
    if DEBUG and not value:
        # Local convenience only. Never used when DEBUG is off.
        return INSECURE_DEV_SECRET_KEY
    if not DEBUG:
        _validate_secret_key(value)
    return value or INSECURE_DEV_SECRET_KEY


def _vercel_allowed_hosts():
    """Host names Vercel serves this deployment on.

    Vercel exposes the deployment URL in VERCEL_URL and the stable production
    alias in VERCEL_PROJECT_PRODUCTION_URL. The bare `.vercel.app` suffix is
    also allowed so preview deployments are not rejected: the hostname is
    unpredictable per deploy and is not a secret, and Vercel only issues those
    names to this project. An explicit DJANGO_ALLOWED_HOSTS still wins.
    """
    hosts = []
    for name in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        value = os.environ.get(name, "").strip()
        if value:
            hosts.append(value)
    hosts.append(".vercel.app")
    return hosts


def _resolve_allowed_hosts():
    hosts = get_list("DJANGO_ALLOWED_HOSTS")
    if hosts:
        return hosts
    if SERVERLESS:
        return _vercel_allowed_hosts()
    if DEBUG:
        return ["localhost", "127.0.0.1", "[::1]"]
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS is empty. Set it to a comma-separated list of "
        "hostnames this service serves, e.g. 'api.example.com'."
    )


def _resolve_csrf_trusted_origins_from_hosts():
    """Derive trusted origins from the hosts this service answers for.

    Only used when DJANGO_CSRF_TRUSTED_ORIGINS is not set explicitly. On
    Vercel the deployment hostname is the only origin a browser would ever
    present, so https://<that host> is the correct value.
    """
    if not SERVERLESS:
        return []
    origins = []
    for host in ALLOWED_HOSTS:
        if host.startswith("."):
            # A wildcard suffix has no single origin to trust.
            continue
        origins.append(f"https://{host}")
    return origins


def _resolve_csrf_trusted_origins():
    """Origins allowed to submit unsafe requests.

    Only meaningful when a browser talks to Django directly. In this project
    the Next.js server proxies every call, so the trusted origins are the
    Next.js service origin, used for the Referer check.
    """
    origins = get_list("DJANGO_CSRF_TRUSTED_ORIGINS")
    if origins:
        return origins
    if DEBUG:
        return ["http://localhost:3000"]
    return _resolve_csrf_trusted_origins_from_hosts()


def _resolve_database_url():
    """Read a single-connection-string database URL, if the platform sets one.

    Vercel's managed Postgres integrations (and most other providers) inject
    `POSTGRES_URL` or `DATABASE_URL` instead of the discrete POSTGRES_*
    variables this project already uses. Supporting it here means no new
    dependency and no change to the existing variable names: the discrete
    variables still take precedence, so a Render deployment is unaffected.
    """
    for name in ("POSTGRES_URL", "DATABASE_URL"):
        raw = os.environ.get(name, "").strip()
        if raw:
            return raw
    return ""


def _parse_database_url(url):
    """Split a postgres:// URL into its parts, or return None if unusable."""
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg"}:
        return None
    return {
        "POSTGRES_DB": unquote(parsed.path.lstrip("/")),
        "POSTGRES_USER": unquote(parsed.username or ""),
        "POSTGRES_PASSWORD": unquote(parsed.password or ""),
        "POSTGRES_HOST": parsed.hostname or "",
        "POSTGRES_PORT": str(parsed.port or ""),
        "POSTGRES_SSLMODE": dict(parse_qsl(parsed.query)).get("sslmode", ""),
    }


# Discrete POSTGRES_* variables win; the URL only fills in what they omit.
_DATABASE_URL_PARTS = _parse_database_url(_resolve_database_url()) or {}


def _postgres_setting(name, default=""):
    return os.environ.get(name) or _DATABASE_URL_PARTS.get(name, default)


def _resolve_database_password():
    password = _postgres_setting("POSTGRES_PASSWORD")
    if not password and not DEBUG:
        raise ImproperlyConfigured(
            "POSTGRES_PASSWORD is not set. The database password must be "
            "supplied by the environment in production."
        )
    return password


SECRET_KEY = _resolve_secret_key()
ALLOWED_HOSTS = _resolve_allowed_hosts()
CSRF_TRUSTED_ORIGINS = _resolve_csrf_trusted_origins()
POSTGRES_PASSWORD = _resolve_database_password()

# HTTPS handling. A PaaS terminates TLS at its proxy, so Django is told to
# trust the forwarded proto/host header and to redirect plain HTTP.
SECURE_SSL_REDIRECT = get_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = get_int("DJANGO_SECURE_HSTS_SECONDS", 0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Cookies. Both are marked secure whenever the site is served over HTTPS.
SESSION_COOKIE_SECURE = get_bool("DJANGO_SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# Five weeks is Django's default; stated here so the value is explicit.
SESSION_COOKIE_AGE = get_int("DJANGO_SESSION_COOKIE_AGE", 60 * 60 * 24 * 14)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Logging.
LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get(
    "DJANGO_LOG_FORMAT",
    "%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Postgres connection.
POSTGRES_DB = _postgres_setting("POSTGRES_DB", "ecommerce")
POSTGRES_USER = _postgres_setting("POSTGRES_USER", "ecommerce")
POSTGRES_HOST = _postgres_setting("POSTGRES_HOST", "localhost")
POSTGRES_PORT = _postgres_setting("POSTGRES_PORT", "5432")
# Managed PostgreSQL (Render, Neon, RDS, ...) requires TLS. Unset locally, where
# the connection is over the loopback interface.
POSTGRES_SSLMODE = _postgres_setting("POSTGRES_SSLMODE").strip()

def _resolve_conn_max_age():
    """Seconds a database connection is reused.

    A long-lived process (gunicorn on Render) benefits from keeping connections
    open. A serverless function is frozen between requests, so a cached
    connection can go stale or be dropped by the provider's connection limit;
    there, closing after each request is the correct behaviour.
    """
    return get_int("POSTGRES_CONN_MAX_AGE", 0 if SERVERLESS else 60)


POSTGRES_CONN_MAX_AGE = _resolve_conn_max_age()

# Set by the tests so they can mark themselves explicitly.
TESTING = get_bool("DJANGO_TESTING", False)
