"""Tests for infrastructure views.

`SimpleTestCase` is used rather than `TestCase` because the project has no
database configured, and these endpoints must not require one.
"""

from django.test import SimpleTestCase
from django.urls import reverse


class HealthViewTests(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_responds_with_json(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response["Content-Type"], "application/json")

    def test_health_rejects_non_get_methods(self):
        response = self.client.post("/api/health/")

        self.assertEqual(response.status_code, 405)
