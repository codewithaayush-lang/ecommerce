"""Order and checkout API.

Checkout is a single database transaction that snapshots prices, decrements
stock and empties the cart. If any step fails, nothing is persisted.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart
from orders.models import Order, OrderItem
from orders.serializers import OrderListSerializer, OrderSerializer
from products.models import Product


def order_queryset(user):
    """The user's orders only, with totals and items precomputed.

    Filtering by `user` is what enforces order ownership: another user's order
    is simply not in this queryset.
    """
    return (
        Order.objects.filter(user=user)
        .annotate(item_count=Sum("items__quantity"))
        .prefetch_related("items")
    )


class OrderListCreateView(APIView):
    """GET /api/orders/ - the user's order history.

    POST /api/orders/ - place an order from the current cart.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = order_queryset(request.user)
        return Response(
            OrderListSerializer(orders, many=True).data, status=status.HTTP_200_OK
        )

    def post(self, request):
        """Convert the cart into an order.

        Steps, all inside one transaction:
          1. load the cart and its items
          2. lock the product rows
          3. re-check stock against the *current* values
          4. create the order
          5. create order items from price/name snapshots
          6. decrement stock
          7. clear the cart
        Any failure raises and rolls the whole thing back.
        """
        with transaction.atomic():
            cart = (
                Cart.objects.select_for_update()
                .filter(user=request.user)
                .first()
            )
            if cart is None:
                raise ValidationError("Your cart is empty.")

            items = list(
                cart.items.select_related("product").order_by("created_at", "id")
            )
            if not items:
                raise ValidationError("Your cart is empty.")

            # Lock the product rows so concurrent checkouts cannot both pass the
            # stock check and drive stock negative.
            product_ids = [item.product_id for item in items]
            locked_products = {
                product.id: product
                for product in Product.objects.select_for_update()
                .filter(id__in=product_ids)
                .order_by("id")
            }

            # Re-check stock now that the rows are locked.
            for item in items:
                product = locked_products[item.product_id]
                if not product.is_active:
                    raise ValidationError(
                        f"{product.name} is no longer available."
                    )
                if item.quantity > product.stock:
                    raise ValidationError(
                        f"Insufficient stock for {product.name}: "
                        f"requested {item.quantity}, {product.stock} available."
                    )

            # Prices and totals are calculated here, never taken from the client.
            order = Order.objects.create(
                user=request.user,
                status=Order.Status.PENDING,
                subtotal=Decimal("0.00"),
                total=Decimal("0.00"),
            )

            subtotal = Decimal("0.00")
            order_items = []
            for item in items:
                product = item.product
                line_total = product.price * item.quantity
                subtotal += line_total

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        # Snapshots: frozen at purchase time.
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=item.quantity,
                        # Set explicitly because bulk_create bypasses save().
                        line_total=line_total,
                    )
                )
                # Decrement stock. F() keeps this atomic at the SQL level.
                Product.objects.filter(pk=product.pk).update(
                    stock=F("stock") - item.quantity
                )

            OrderItem.objects.bulk_create(order_items)

            order.subtotal = subtotal
            order.total = subtotal
            order.save(update_fields=["subtotal", "total", "updated_at"])

            # The cart is emptied as part of the same transaction.
            cart.items.all().delete()

        order.refresh_from_db()
        return Response(
            OrderSerializer(order_queryset(request.user).get(pk=order.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    """GET /api/orders/<id>/ - one of the user's own orders."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(order_queryset(request.user), pk=pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    """POST /api/orders/<id>/cancel/ - withdraw an early-status order."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update().filter(user=request.user), pk=pk
            )

            if order.status == Order.Status.CANCELLED:
                raise ValidationError("This order is already cancelled.")
            if not order.can_cancel:
                raise ValidationError(
                    f"An order with status '{order.get_status_display()}' "
                    "can no longer be cancelled."
                )

            # Put the reserved units back on sale.
            items = list(order.items.all())
            for item in items:
                Product.objects.filter(pk=item.product_id).update(
                    stock=F("stock") + item.quantity
                )

            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])

        order.refresh_from_db()
        return Response(
            OrderSerializer(order_queryset(request.user).get(pk=order.pk)).data,
            status=status.HTTP_200_OK,
        )
