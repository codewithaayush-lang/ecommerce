# Meridian Goods — Backend

Django + Django REST Framework API for the storefront.

This step contains **only** the backend skeleton and a health-check endpoint.
There is no database, no models, no serializers, and no authentication yet.

## Requirements

- Python 3.14 (3.10+ works)
- No database server required yet

## Getting started

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install django djangorestframework
.venv/bin/python manage.py runserver
```

Verify the API is up:

```bash
curl http://localhost:8000/api/health/
# {"status":"ok"}
```

## Scripts / commands

| Command                                | Purpose                          |
| -------------------------------------- | -------------------------------- |
| `.venv/bin/python manage.py runserver` | Start the dev server on :8000    |
| `.venv/bin/python manage.py check`     | Run Django system checks         |
| `.venv/bin/python manage.py test`      | Run the test suite               |

On Windows, replace `.venv/bin/` with `.venv\Scripts\`.

## Structure

```
backend/
├── manage.py
├── .env.example            # Template for environment variables
├── config/                 # Project settings package
│   ├── settings.py         # Settings, read from environment variables
│   ├── urls.py             # Root URLconf; mounts /api/ routes
│   ├── views.py            # Health-check view
│   ├── tests.py            # Tests for infrastructure views
│   ├── asgi.py / wsgi.py   # ASGI/WSGI entry points
├── products/               # App for the product domain (no models yet)
│   ├── models.py           # Empty
│   ├── views.py            # Empty
│   ├── tests.py            # Empty
│   └── migrations/
└── .venv/                  # Virtual environment (gitignored)
```

## Current state and intentional omissions

- **No database is configured.** `DATABASES = {}` makes Django fall back to the
  `dummy` backend, so any accidental query raises `ImproperlyConfigured` instead
  of silently creating a SQLite file. PostgreSQL is added in a later step.
- **No authentication.** `DEFAULT_AUTHENTICATION_CLASSES` is empty and
  permissions default to `AllowAny`.
- **JSON only.** The browsable API renderer is disabled, so every response is
  `application/json`.
- **`manage.py check --deploy` reports 6 warnings** (HSTS, secure cookies, the
  dev secret key, `DEBUG=True`). These are expected for local development and
  are addressed when production settings are added.

## Configuration

Settings read from the environment; see `.env.example` for the supported
variables. Copy it to `.env` and fill in real values when they are needed:

```bash
cp .env.example .env
```

Note that `.env` is gitignored and is **not** loaded automatically yet — no
dotenv dependency is installed. Environment variables must be exported into the
shell (or set by your process manager) until that is added.
