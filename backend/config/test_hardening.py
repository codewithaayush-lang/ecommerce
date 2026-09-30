"""Tests for production hardening: error handling and config validation.

These run with DEBUG=False (the Django test runner forces it), which is the
configuration that matters for error handling.
"""

import json
import os
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings

import config.views as config_views
from config import env as env_module
from django.core.exceptions import ImproperlyConfigured


class ApiErrorHandlingTests(SimpleTestCase):
    """API errors must be JSON and must never leak internals."""

    def test_unmatched_api_path_returns_json_404(self):
        response = self.client.get("/api/definitely-not-a-route/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_unmatched_non_api_path_keeps_html(self):
        response = self.client.get("/not-an-api-path/")

        self.assertEqual(response.status_code, 404)
        self.assertIn("text/html", response["Content-Type"])

    def test_handler500_returns_json_for_api_paths(self):
        # Django invokes handler500 with only the request.
        response = config_views.server_error(self._request("/api/cart/"))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.content.decode()),
            {"detail": "An unexpected error occurred."},
        )

    def test_handler500_does_not_leak_details(self):
        response = config_views.server_error(self._request("/api/cart/"))
        body = response.content.decode()

        self.assertNotIn("Traceback", body)
        self.assertNotIn("/home/", body)
        self.assertNotIn("DATABASES", body)

    def test_drf_exception_handler_sanitises_unknown_exceptions(self):
        """An exception type DRF does not know must not reach the client."""
        from config.errors import api_exception_handler

        boom = RuntimeError("INTERNAL SECRET /etc/passwd")
        response = api_exception_handler(boom, {"request": self._request("/api/x/")})

        self.assertEqual(response.status_code, 500)
        # A DRF Response is lazily rendered; force it before reading content.
        body = json.dumps(response.data)
        self.assertIn("An unexpected error occurred.", body)
        self.assertNotIn("INTERNAL SECRET", body)
        self.assertNotIn("Traceback", body)

    def test_known_errors_keep_their_useful_message(self):
        """Auth and validation errors stay specific; only unknowns go generic."""
        response = self.client.post(
            "/api/cart/items/", {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication credentials", response.json()["detail"])

    def _request(self, path):
        from django.test import RequestFactory

        return RequestFactory().get(path)


class EnvironmentValidationTests(SimpleTestCase):
    """Production configuration must fail fast."""

    def test_missing_secret_key_is_rejected_in_production(self):
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": ""}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_secret_key()
        self.assertIn("DJANGO_SECRET_KEY is not set", str(ctx.exception))

    def test_development_fallback_secret_is_rejected_in_production(self):
        with mock.patch.dict(
            os.environ,
            {"DJANGO_SECRET_KEY": env_module.INSECURE_DEV_SECRET_KEY},
            clear=False,
        ):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_secret_key()
        self.assertIn("development fallback", str(ctx.exception))

    def test_short_secret_key_is_rejected_in_production(self):
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": "tooshort"}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_secret_key()
        self.assertIn("at least 50", str(ctx.exception))

    def test_low_entropy_secret_key_is_rejected(self):
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": "a" * 60}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_secret_key()
        self.assertIn("random enough", str(ctx.exception))

    def test_strong_secret_key_is_accepted(self):
        # 60 characters containing well over 5 distinct values.
        strong = "aB3dE5fG7hJ9kL2mN4pQ6rS8tU1vW3xY5zC7eR9gT2hV4jK6mN8pQ1rS5tU"
        self.assertGreaterEqual(len(strong), 50)
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": strong}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                self.assertEqual(env_module._resolve_secret_key(), strong)

    def test_empty_allowed_hosts_is_rejected_in_production(self):
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": ""}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_allowed_hosts()
        self.assertIn("ALLOWED_HOSTS is empty", str(ctx.exception))

    def test_allowed_hosts_falls_back_to_localhost_in_development(self):
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": ""}, clear=False):
            with mock.patch.object(env_module, "DEBUG", True):
                self.assertIn("localhost", env_module._resolve_allowed_hosts())

    def test_missing_database_password_is_rejected_in_production(self):
        with mock.patch.dict(os.environ, {"POSTGRES_PASSWORD": ""}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    env_module._resolve_database_password()
        self.assertIn("POSTGRES_PASSWORD", str(ctx.exception))


class VercelEnvironmentTests(SimpleTestCase):
    """The defaults that adapt when the app runs on Vercel."""

    VERCEL_ENV = {
        "VERCEL": "1",
        "VERCEL_URL": "myapi-abc123.vercel.app",
        "VERCEL_PROJECT_PRODUCTION_URL": "myapi.vercel.app",
        "DJANGO_ALLOWED_HOSTS": "",
    }

    def _under_vercel(self):
        return mock.patch.dict(os.environ, self.VERCEL_ENV, clear=False)

    def test_serverless_is_detected(self):
        with self._under_vercel():
            self.assertTrue(env_module._detect_serverless())

    def test_not_serverless_outside_vercel(self):
        with mock.patch.dict(
            os.environ, {"VERCEL": "", "VERCEL_URL": ""}, clear=False
        ):
            self.assertFalse(env_module._detect_serverless())

    def test_allowed_hosts_fall_back_to_the_deployment_hostnames(self):
        with self._under_vercel():
            with mock.patch.object(env_module, "SERVERLESS", True):
                hosts = env_module._resolve_allowed_hosts()
        self.assertIn("myapi-abc123.vercel.app", hosts)
        self.assertIn("myapi.vercel.app", hosts)
        # Preview deployments get a new hostname on every build, so the suffix
        # has to be allowed too.
        self.assertIn(".vercel.app", hosts)

    def test_explicit_allowed_hosts_still_win_on_vercel(self):
        env = dict(self.VERCEL_ENV, DJANGO_ALLOWED_HOSTS="api.example.com")
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(env_module, "SERVERLESS", True):
                hosts = env_module._resolve_allowed_hosts()
        self.assertEqual(hosts, ["api.example.com"])

    def test_allowed_hosts_are_still_required_off_vercel(self):
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": ""}, clear=False):
            with mock.patch.object(env_module, "DEBUG", False):
                with mock.patch.object(env_module, "SERVERLESS", False):
                    with self.assertRaises(ImproperlyConfigured):
                        env_module._resolve_allowed_hosts()

    def test_csrf_origins_derive_from_the_deployment_hosts(self):
        with self._under_vercel():
            with mock.patch.object(env_module, "DEBUG", False):
                with mock.patch.object(env_module, "SERVERLESS", True):
                    with mock.patch.object(
                        env_module,
                        "ALLOWED_HOSTS",
                        ["myapi-abc123.vercel.app", ".vercel.app"],
                    ):
                        origins = env_module._resolve_csrf_trusted_origins()
        self.assertIn("https://myapi-abc123.vercel.app", origins)
        # A wildcard has no single origin, so it must not become a trusted one.
        self.assertNotIn("https://.vercel.app", origins)

    def test_database_url_is_used_when_discrete_variables_are_absent(self):
        url = "postgresql://user:p%40ss@db.example.com:5432/shop?sslmode=require"
        with mock.patch.dict(
            os.environ, {"POSTGRES_URL": url, "DATABASE_URL": ""}, clear=False
        ):
            parts = env_module._parse_database_url(url)
        self.assertEqual(parts["POSTGRES_DB"], "shop")
        self.assertEqual(parts["POSTGRES_USER"], "user")
        # The percent-encoded password must be decoded, not passed through raw.
        self.assertEqual(parts["POSTGRES_PASSWORD"], "p@ss")
        self.assertEqual(parts["POSTGRES_HOST"], "db.example.com")
        self.assertEqual(parts["POSTGRES_PORT"], "5432")
        self.assertEqual(parts["POSTGRES_SSLMODE"], "require")

    def test_non_postgres_url_is_ignored(self):
        self.assertIsNone(env_module._parse_database_url("mysql://u:p@h:3306/db"))

    def test_discrete_variables_take_precedence_over_the_url(self):
        url_parts = {"POSTGRES_HOST": "url-host"}
        with mock.patch.dict(
            os.environ, {"POSTGRES_HOST": ""}, clear=False
        ):
            with mock.patch.object(
                env_module, "_DATABASE_URL_PARTS", url_parts
            ):
                # Unset in the environment, so the value comes from the URL.
                self.assertEqual(
                    env_module._postgres_setting("POSTGRES_HOST"), "url-host"
                )
        with mock.patch.dict(
            os.environ, {"POSTGRES_HOST": "explicit-host"}, clear=False
        ):
            with mock.patch.object(
                env_module, "_DATABASE_URL_PARTS", url_parts
            ):
                # Set in the environment, so the URL is ignored.
                self.assertEqual(
                    env_module._postgres_setting("POSTGRES_HOST"), "explicit-host"
                )

    def test_connections_are_not_reused_on_vercel(self):
        with mock.patch.dict(
            os.environ, {"POSTGRES_CONN_MAX_AGE": ""}, clear=False
        ):
            with mock.patch.object(env_module, "SERVERLESS", True):
                self.assertEqual(env_module._resolve_conn_max_age(), 0)
            # A long-lived process keeps the connection open.
            with mock.patch.object(env_module, "SERVERLESS", False):
                self.assertEqual(env_module._resolve_conn_max_age(), 60)

    def test_conn_max_age_can_be_set_explicitly(self):
        with mock.patch.dict(
            os.environ, {"POSTGRES_CONN_MAX_AGE": "120"}, clear=False
        ):
            with mock.patch.object(env_module, "SERVERLESS", True):
                self.assertEqual(env_module._resolve_conn_max_age(), 120)


class SecuritySettingTests(SimpleTestCase):
    def test_cookies_are_http_only_and_lax(self):
        from django.conf import settings

        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "Lax")

    def test_static_url_is_absolute(self):
        from django.conf import settings

        self.assertTrue(settings.STATIC_URL.startswith("/"))

    def test_debug_is_false_in_the_test_environment(self):
        from django.conf import settings

        # The test runner forces DEBUG off; error handling depends on it.
        self.assertFalse(settings.DEBUG)


@override_settings(DEBUG=True)
class HostHeaderTests(TestCase):
    def test_disallowed_host_is_rejected(self):
        response = self.client.get(
            "/api/health/", headers={"host": "evil.example.com"}
        )

        self.assertEqual(response.status_code, 400)
