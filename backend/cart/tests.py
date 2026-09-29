"""Tests for the cart API.

Every test uses the real HTTP surface so authentication, permissions and
ownership scoping are all exercised.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Category, Product

User = get_user_model()


class CartTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Kitchen", slug="kitchen", description="Tools"
        )
        self.kettle = Product.objects.create(
            name="Kettle",
            slug="kettle",
            description="A kettle.",
            price=Decimal("50.00"),
            category=self.category,
            stock=10,
        )
        self.mug = Product.objects.create(
            name="Mug",
            slug="mug",
            description="A mug.",
            price=Decimal("5.00"),
            category=self.category,
            stock=3,
        )
        self.inactive = Product.objects.create(
            name="Old Thing",
            slug="old-thing",
            description="Retired.",
            price=Decimal("1.00"),
            category=self.category,
            stock=5,
            is_active=False,
        )

        self.user = User.objects.create_user(
            username="shopper", email="shopper@example.com", password="Str0ngPassw0rd!"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="Str0ngPassw0rd!"
        )

        self.cart_url = reverse("cart:cart-detail")
        self.items_url = reverse("cart:cart-item-list")
        self.clear_url = reverse("cart:cart-clear")

    def add_item(self, product, quantity=1):
        return self.client.post(
            self.items_url, {"product_id": product.id, "quantity": quantity}, format="json"
        )


class CartAccessTests(CartTestCase):
    def test_cart_requires_authentication(self):
        for method, url in (
            ("get", self.cart_url),
            ("post", self.items_url),
            ("delete", self.clear_url),
        ):
            response = getattr(self.client, method)(url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                msg=f"{method.upper()} {url} should require auth",
            )

    def test_item_detail_requires_authentication(self):
        self.client.force_authenticate(self.user)
        item = CartItem.objects.create(
            cart=Cart.objects.create(user=self.user), product=self.kettle, quantity=1
        )
        self.client.logout()
        url = reverse("cart:cart-item-detail", args=[item.id])

        self.assertEqual(self.client.patch(url, {}, format="json").status_code, 401)
        self.assertEqual(self.client.delete(url, format="json").status_code, 401)

    def test_empty_cart_is_created_on_first_access(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["subtotal"], "0.00")
        self.assertEqual(response.data["item_count"], 0)


class CartItemTests(CartTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)

    def test_add_item(self):
        response = self.add_item(self.kettle, 2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 2)
        self.assertEqual(response.data["unit_price"], "50.00")
        self.assertEqual(response.data["line_total"], "100.00")
        self.assertEqual(CartItem.objects.count(), 1)

    def test_adding_same_product_twice_increases_quantity(self):
        self.add_item(self.kettle, 2)
        response = self.add_item(self.kettle, 3)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 5)
        # A duplicate row must not be created.
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_nonexistent_product_is_rejected(self):
        response = self.client.post(
            self.items_url, {"product_id": 99999, "quantity": 1}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_inactive_product_is_rejected(self):
        response = self.add_item(self.inactive)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_quantity_beyond_stock_is_rejected(self):
        response = self.add_item(self.kettle, 11)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_combined_quantity_beyond_stock_is_rejected(self):
        self.add_item(self.mug, 3)

        response = self.add_item(self.mug, 1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.get()
        # The failed increment must not have been written.
        self.assertEqual(item.quantity, 3)

    def test_zero_quantity_is_rejected(self):
        response = self.add_item(self.kettle, 0)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_quantity_is_rejected(self):
        response = self.add_item(self.kettle, -5)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_updates_quantity(self):
        created = self.add_item(self.kettle, 1)
        url = reverse("cart:cart-item-detail", args=[created.data["id"]])

        response = self.client.patch(url, {"quantity": 4}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 4)
        self.assertEqual(response.data["line_total"], "200.00")

    def test_patch_to_zero_is_rejected(self):
        created = self.add_item(self.kettle, 1)
        url = reverse("cart:cart-item-detail", args=[created.data["id"]])

        response = self.client.patch(url, {"quantity": 0}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CartItem.objects.get().quantity, 1)

    def test_patch_beyond_stock_is_rejected(self):
        created = self.add_item(self.kettle, 1)
        url = reverse("cart:cart-item-detail", args=[created.data["id"]])

        response = self.client.patch(url, {"quantity": 99}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_removes_item(self):
        created = self.add_item(self.kettle, 1)
        url = reverse("cart:cart-item-detail", args=[created.data["id"]])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_clear_empties_cart(self):
        self.add_item(self.kettle, 1)
        self.add_item(self.mug, 1)

        response = self.client.delete(self.clear_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)
        # The cart itself survives, only its lines are removed.
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_cart_totals_are_calculated_from_live_prices(self):
        self.add_item(self.kettle, 2)
        self.add_item(self.mug, 2)

        response = self.client.get(self.cart_url)

        # 2*50 + 2*5
        self.assertEqual(response.data["subtotal"], "110.00")
        self.assertEqual(response.data["item_count"], 4)

        # A price change is reflected immediately: totals are never stored.
        self.kettle.price = Decimal("40.00")
        self.kettle.save()

        response = self.client.get(self.cart_url)
        self.assertEqual(response.data["subtotal"], "90.00")

    def test_max_quantity_reports_remaining_stock(self):
        created = self.add_item(self.mug, 2)

        self.assertEqual(created.data["max_quantity"], 1)


class CartIsolationTests(CartTestCase):
    def test_user_cannot_see_another_users_cart(self):
        self.client.force_authenticate(self.other)
        self.add_item(self.kettle, 1)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.cart_url)

        self.assertEqual(response.data["items"], [])

    def test_user_cannot_modify_another_users_item(self):
        self.client.force_authenticate(self.other)
        created = self.add_item(self.kettle, 1)
        url = reverse("cart:cart-item-detail", args=[created.data["id"]])

        self.client.force_authenticate(self.user)
        patch = self.client.patch(url, {"quantity": 9}, format="json")
        delete = self.client.delete(url)

        self.assertEqual(patch.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete.status_code, status.HTTP_404_NOT_FOUND)
        # The other user's item is untouched.
        self.assertEqual(CartItem.objects.get().quantity, 1)

    def test_clearing_cart_does_not_touch_other_users_cart(self):
        self.client.force_authenticate(self.other)
        self.add_item(self.kettle, 1)

        self.client.force_authenticate(self.user)
        self.client.delete(self.clear_url)

        self.assertEqual(CartItem.objects.count(), 1)


class CartQueryCountTests(CartTestCase):
    def _query_count_for_cart(self, item_count):
        """Add `item_count` lines and return how many queries the read costs."""
        self.client.force_authenticate(self.user)
        cart = Cart.objects.get_or_create(user=self.user)[0]
        # One row per product per cart, so pad the product table to reach the
        # requested line count.
        while Product.objects.count() < item_count:
            index = Product.objects.count()
            Product.objects.create(
                name=f"Filler {index}",
                slug=f"filler-{index}",
                description="Padding for the query count test.",
                price=Decimal("1.00"),
                category=self.category,
                stock=5,
            )
        products = list(Product.objects.all())
        CartItem.objects.all().delete()
        for product in products[:item_count]:
            CartItem.objects.create(cart=cart, product=product, quantity=1)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(self.cart_url)
        self.assertEqual(len(response.data["items"]), item_count)
        return len(captured.captured_queries)

    def test_cart_read_is_not_n_plus_one(self):
        """The number of queries must not grow with the number of cart lines."""
        few = self._query_count_for_cart(3)
        many = self._query_count_for_cart(12)

        # 4 queries: cart, items, products, categories. Constant either way.
        self.assertEqual(few, many)
        self.assertEqual(many, 4)
