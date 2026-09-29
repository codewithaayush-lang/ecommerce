"""Tests for checkout and the order API."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from products.models import Category, Product

User = get_user_model()


class OrderTestCase(APITestCase):
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
            stock=4,
        )

        self.user = User.objects.create_user(
            username="shopper", email="shopper@example.com", password="Str0ngPassw0rd!"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="Str0ngPassw0rd!"
        )

        self.orders_url = reverse("orders:order-list")
        self.client.force_authenticate(self.user)

    def add_to_cart(self, product, quantity=1, user=None):
        user = user or self.user
        cart, _ = Cart.objects.get_or_create(user=user)
        return CartItem.objects.create(
            cart=cart, product=product, quantity=quantity
        )

    def place_order(self):
        return self.client.post(self.orders_url, {}, format="json")


class OrderAccessTests(OrderTestCase):
    def test_order_endpoints_require_authentication(self):
        self.client.logout()

        self.assertEqual(self.client.get(self.orders_url).status_code, 401)
        self.assertEqual(self.client.post(self.orders_url, {}, format="json").status_code, 401)

    def test_order_detail_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("orders:order-detail", args=[1]))

        self.assertEqual(response.status_code, 401)

    def test_cancel_requires_authentication(self):
        self.client.logout()

        response = self.client.post(reverse("orders:order-cancel", args=[1]), format="json")

        self.assertEqual(response.status_code, 401)


class CheckoutTests(OrderTestCase):
    def test_checkout_with_empty_cart_is_rejected(self):
        response = self.place_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_successful_checkout_creates_order_with_items(self):
        self.add_to_cart(self.kettle, 2)
        self.add_to_cart(self.mug, 1)

        response = self.place_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(response.data["item_count"], 3)

    def test_totals_are_calculated_server_side(self):
        self.add_to_cart(self.kettle, 2)   # 100.00
        self.add_to_cart(self.mug, 3)      # 15.00

        self.place_order()

        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal("115.00"))
        self.assertEqual(order.total, Decimal("115.00"))

    def test_line_totals_are_calculated(self):
        self.add_to_cart(self.kettle, 2)

        self.place_order()

        item = OrderItem.objects.get()
        self.assertEqual(item.unit_price, Decimal("50.00"))
        self.assertEqual(item.line_total, Decimal("100.00"))

    def test_client_supplied_prices_are_ignored(self):
        self.add_to_cart(self.kettle, 1)

        response = self.client.post(
            self.orders_url,
            # A malicious client tries to dictate its own totals.
            {"total": "0.01", "subtotal": "0.01", "items": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("50.00"))

    def test_order_items_snapshot_name_and_price(self):
        self.add_to_cart(self.kettle, 1)

        self.place_order()
        item = OrderItem.objects.get()

        self.assertEqual(item.product_name, "Kettle")
        self.assertEqual(item.unit_price, Decimal("50.00"))

    def test_history_is_not_recalculated_from_live_price(self):
        self.add_to_cart(self.kettle, 2)
        self.place_order()

        # The product is later repriced and renamed.
        self.kettle.price = Decimal("999.00")
        self.kettle.name = "Renamed Kettle"
        self.kettle.save()

        order = Order.objects.get()
        item = order.items.get()

        self.assertEqual(item.unit_price, Decimal("50.00"))
        self.assertEqual(item.line_total, Decimal("100.00"))
        self.assertEqual(item.product_name, "Kettle")
        self.assertEqual(order.total, Decimal("100.00"))

    def test_checkout_reduces_stock(self):
        self.add_to_cart(self.kettle, 3)

        self.place_order()

        self.kettle.refresh_from_db()
        self.assertEqual(self.kettle.stock, 7)

    def test_checkout_clears_the_cart(self):
        self.add_to_cart(self.kettle, 1)
        self.add_to_cart(self.mug, 1)

        self.place_order()

        self.assertEqual(CartItem.objects.count(), 0)
        # The cart row itself remains.
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_checkout_rejects_quantity_above_stock(self):
        # Put more in the cart than exists, bypassing cart validation.
        self.add_to_cart(self.mug, 10)

        response = self.place_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.mug.refresh_from_db()
        self.assertEqual(self.mug.stock, 4)

    def test_failed_checkout_rolls_back_everything(self):
        self.add_to_cart(self.kettle, 1)
        self.add_to_cart(self.mug, 99)  # fails the stock check

        self.place_order()

        # No order, no items, stock untouched, cart intact.
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.kettle.refresh_from_db()
        self.mug.refresh_from_db()
        self.assertEqual(self.kettle.stock, 10)
        self.assertEqual(self.mug.stock, 4)
        self.assertEqual(CartItem.objects.count(), 2)

    def test_stock_never_goes_negative(self):
        self.add_to_cart(self.mug, 4)
        self.add_to_cart(self.kettle, 10)

        self.place_order()

        self.mug.refresh_from_db()
        self.kettle.refresh_from_db()
        self.assertEqual(self.mug.stock, 0)
        self.assertEqual(self.kettle.stock, 0)
        self.assertGreaterEqual(self.mug.stock, 0)
        self.assertGreaterEqual(self.kettle.stock, 0)

    def test_inactive_product_blocks_checkout(self):
        product = Product.objects.create(
            name="Retired",
            slug="retired",
            description="Gone.",
            price=Decimal("9.00"),
            category=self.category,
            stock=5,
            is_active=False,
        )
        self.add_to_cart(product, 1)

        response = self.place_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)


class OrderListDetailTests(OrderTestCase):
    def setUp(self):
        super().setUp()
        self.add_to_cart(self.kettle, 2)
        self.place_order()
        self.order = Order.objects.get()

    def test_list_returns_user_orders(self):
        response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.order.id)
        self.assertEqual(response.data[0]["total"], "100.00")

    def test_list_excludes_other_users_orders(self):
        self.client.force_authenticate(self.other)

        response = self.client.get(self.orders_url)

        self.assertEqual(response.data, [])

    def test_detail_returns_order_with_items(self):
        response = self.client.get(reverse("orders:order-detail", args=[self.order.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.PENDING)
        self.assertEqual(response.data["total"], "100.00")
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product_name"], "Kettle")

    def test_user_cannot_view_another_users_order(self):
        self.client.force_authenticate(self.other)

        response = self.client.get(reverse("orders:order-detail", args=[self.order.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_order_returns_404(self):
        response = self.client.get(reverse("orders:order-detail", args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_detail_does_not_expose_price_hash(self):
        response = self.client.get(reverse("orders:order-detail", args=[self.order.id]))

        self.assertNotIn("password", response.content.decode().lower())


class OrderCancellationTests(OrderTestCase):
    def setUp(self):
        super().setUp()
        self.add_to_cart(self.kettle, 2)
        self.place_order()
        self.order = Order.objects.get()

    def cancel(self, order=None):
        order = order or self.order
        return self.client.post(
            reverse("orders:order-cancel", args=[order.id]), {}, format="json"
        )

    def test_cancel_marks_order_cancelled(self):
        response = self.cancel()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_cancel_restores_stock(self):
        self.kettle.refresh_from_db()
        self.assertEqual(self.kettle.stock, 8)

        self.cancel()

        self.kettle.refresh_from_db()
        self.assertEqual(self.kettle.stock, 10)

    def test_cancel_preserves_snapshot_totals(self):
        self.cancel()

        self.order.refresh_from_db()
        self.assertEqual(self.order.total, Decimal("100.00"))
        self.assertEqual(self.order.items.get().unit_price, Decimal("50.00"))

    def test_cannot_cancel_twice(self):
        self.cancel()

        response = self.cancel()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_a_shipped_order(self):
        self.order.status = Order.Status.SHIPPED
        self.order.save()

        response = self.cancel()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)

    def test_cannot_cancel_another_users_order(self):
        self.client.force_authenticate(self.other)

        response = self.cancel()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_user_cannot_set_status_directly(self):
        # There is no write endpoint for status; a PATCH must not exist.
        response = self.client.patch(
            reverse("orders:order-detail", args=[self.order.id]),
            {"status": "delivered"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
