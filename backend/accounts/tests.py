"""Tests for authentication endpoints."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")
        self.me_url = reverse("accounts:me")

    def create_user(self, username="shopper", email="shopper@example.com",
                    password="Str0ngPassw0rd!"):
        return User.objects.create_user(
            username=username, email=email, password=password
        )


class RegistrationTests(AuthenticationTestCase):
    def test_registration_succeeds(self):
        response = self.client.post(
            self.register_url,
            {"username": "newuser", "email": "new@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser")
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_registration_never_returns_password(self):
        response = self.client.post(
            self.register_url,
            {"username": "newuser", "email": "new@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertNotIn("password", response.data)
        self.assertNotIn("Str0ngPassw0rd!", response.content.decode())

    def test_password_is_hashed_not_stored_plaintext(self):
        self.client.post(
            self.register_url,
            {"username": "newuser", "email": "new@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        user = User.objects.get(username="newuser")
        self.assertNotEqual(user.password, "Str0ngPassw0rd!")
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_duplicate_username_is_rejected(self):
        self.create_user(username="taken")

        response = self.client.post(
            self.register_url,
            {"username": "taken", "email": "other@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_duplicate_email_is_rejected(self):
        self.create_user(username="first", email="dup@example.com")

        response = self.client.post(
            self.register_url,
            {"username": "second", "email": "dup@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_weak_password_is_rejected_by_django_validators(self):
        response = self.client.post(
            self.register_url,
            {"username": "newuser", "email": "new@example.com",
             "password": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_invalid_email_is_rejected(self):
        response = self.client.post(
            self.register_url,
            {"username": "newuser", "email": "not-an-email",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_signs_the_user_in(self):
        response = self.client.post(
            self.register_url,
            {"username": "newuser", "email": "new@example.com",
             "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.wsgi_request.user.is_authenticated, True)


class LoginLogoutTests(AuthenticationTestCase):
    def test_login_succeeds_and_returns_user(self):
        self.create_user()

        response = self.client.post(
            self.login_url,
            {"username": "shopper", "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "shopper")
        self.assertNotIn("password", response.data)

    def test_login_establishes_a_session(self):
        self.create_user()

        self.client.post(
            self.login_url,
            {"username": "shopper", "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertIn("sessionid", self.client.cookies)

    def test_login_with_wrong_password_is_rejected(self):
        self.create_user()

        response = self.client.post(
            self.login_url,
            {"username": "shopper", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("sessionid", self.client.cookies)

    def test_login_with_unknown_user_is_rejected(self):
        response = self.client.post(
            self.login_url,
            {"username": "ghost", "password": "Str0ngPassw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_error_does_not_reveal_whether_user_exists(self):
        self.create_user()

        wrong_password = self.client.post(
            self.login_url,
            {"username": "shopper", "password": "wrong"},
            format="json",
        )
        unknown_user = self.client.post(
            self.login_url,
            {"username": "ghost", "password": "wrong"},
            format="json",
        )

        self.assertEqual(wrong_password.data, unknown_user.data)

    def test_logout_terminates_the_session(self):
        self.create_user()
        self.client.post(
            self.login_url,
            {"username": "shopper", "password": "Str0ngPassw0rd!"},
            format="json",
        )

        response = self.client.post(self.logout_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        me = self.client.get(self.me_url)
        self.assertEqual(me.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(AuthenticationTestCase):
    def test_me_returns_authenticated_user(self):
        user = self.create_user()
        self.client.force_authenticate(user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "shopper")
        self.assertNotIn("password", response.data)

    def test_me_returns_401_when_unauthenticated(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CsrfEndpointTests(AuthenticationTestCase):
    def test_csrf_endpoint_issues_a_token(self):
        response = self.client.get(reverse("accounts:csrf"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["csrf_token"])
        self.assertIn("csrftoken", response.cookies)
