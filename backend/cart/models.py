"""Cart models.

A user has at most one cart. Line totals and subtotals are never stored:
they are always calculated from the live Product price at read time, so a
price change in the catalog is reflected immediately and correctly.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Cart(models.Model):
    """A single persistent cart per user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(models.Model):
    """One product line in a cart.

    A product appears at most once per cart; adding it again increases the
    existing row's quantity.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            # One row per product per cart.
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart",
            ),
            # Guards against a zero or negative quantity reaching the database,
            # even if a caller bypasses serializer validation.
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="cart_item_quantity_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["cart", "product"], name="cart_item_cart_product_idx"),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product}"

    @property
    def line_total(self):
        """Quantity x current unit price. Calculated, never stored."""
        return self.product.price * self.quantity
