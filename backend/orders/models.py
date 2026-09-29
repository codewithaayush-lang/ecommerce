"""Order models.

An Order records a completed purchase. OrderItem stores a snapshot of the
product name and unit price at the moment of purchase, so historical orders
never change when the live Product row is later edited or repriced.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models import Sum


class Order(models.Model):
    """A placed order belonging to one user."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    # An order can be withdrawn while it has not entered fulfilment.
    CANCELLABLE_STATUSES = {Status.PENDING, Status.CONFIRMED}

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Totals are server-calculated and frozen at purchase time.
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="order_user_created_idx"),
        ]

    def __str__(self):
        return f"Order {self.pk} ({self.status})"

    @property
    def can_cancel(self):
        return self.status in self.CANCELLABLE_STATUSES

    def recalculate_totals(self):
        """Recompute subtotal/total from the stored line totals.

        Uses the snapshotted `line_total` values, never the current Product
        price.
        """
        subtotal = self.items.aggregate(total=Sum("line_total"))["total"] or Decimal("0")
        self.subtotal = subtotal
        # No shipping or tax is modelled yet, so total equals subtotal.
        self.total = subtotal
        return subtotal


class OrderItem(models.Model):
    """A purchased product line with frozen name and price snapshots."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    # Kept for referential integrity and analytics. The snapshot fields below
    # are what history is rendered from.
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    # Snapshots: written once at purchase time, never recomputed.
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        # line_total is derived from the snapshot, so it can never drift from
        # unit_price * quantity.
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
