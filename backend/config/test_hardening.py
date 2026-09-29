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
