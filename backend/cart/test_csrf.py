"""Tests proving CSRF protection is enforced on authenticated writes.

These use a client with `enforce_csrf_checks=True`, so DRF's
`SessionAuthentication` CSRF validation behaves exactly as it would in a real
browser request. The point is to show that the API is *not* csrf_exempt.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Category, Product

User = get_user_model()


class CsrfEnforcementTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Kitchen", slug="kitchen", description="Tools"
        )
        self.product = Product.objects.create(
            name="Kettle",
            slug="kettle",
            description="A kettle.",
            price=Decimal("50.00"),
            category=self.category,
            stock=5,
        )
        self.user = User.objects.create_user(
            username="shopper", email="shopper@example.com", password="Str0ngPassw0rd!"
        )

        # A client that actually enforces CSRF, unlike the default test client.
        self.strict = Client(enforce_csrf_checks=True)
        self.strict.force_login(self.user)

    def test_add_to_cart_without_csrf_token_is_rejected(self):
        response = self.strict.post(
            reverse("cart:cart-item-list"),
            data={"product_id": self.product.id, "quantity": 1},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout_without_csrf_token_is_rejected(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        response = self.strict.post(reverse("orders:order-list"), data={})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.product.__class__.objects.get().stock, 5
        )

    def test_logout_without_csrf_token_is_rejected(self):
        response = self.strict.post(reverse("accounts:logout"), data={})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reads_do_not_require_csrf(self):
        # Safe methods are unaffected by CSRF enforcement.
        response = self.strict.get(reverse("cart:cart-detail"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
