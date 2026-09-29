"""Cart API.

Every endpoint is scoped to `request.user.cart`, so one user can never read or
modify another user's cart. All stock and price checks happen on the server.
"""

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from cart.serializers import CartItemSerializer, CartSerializer


def get_user_cart(user):
    """Return the user's cart, creating it on first use."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def prefetched_cart(user):
    """Cart with its items and their products already loaded."""
    cart = (
        Cart.objects.filter(user=user)
        .prefetch_related("items__product__category")
        .first()
    )
    if cart is None:
        cart = Cart.objects.create(user=user)
    return cart


class CartDetailView(APIView):
    """GET /api/cart/ - the authenticated user's cart."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = prefetched_cart(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemListView(APIView):
    """POST /api/cart/items/ - add a product to the cart."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            cart = get_user_cart(request.user)
            item = (
                CartItem.objects.select_for_update()
                .filter(cart=cart, product=product)
                .first()
            )

            # Adding a product that is already in the cart increases the
            # existing row rather than creating a duplicate.
            new_quantity = quantity if item is None else item.quantity + quantity

            if new_quantity > product.stock:
                # Raised inside the atomic block, so nothing is written.
                raise ValidationError(
                    {
                        "quantity": (
                            f"Only {product.stock} of this product "
                            f"{'is' if product.stock == 1 else 'are'} in stock."
                        )
                    }
                )

            if item is None:
                item = CartItem.objects.create(
                    cart=cart, product=product, quantity=new_quantity
                )
            else:
                item.quantity = new_quantity
                item.save(update_fields=["quantity", "updated_at"])

        return Response(
            CartItemSerializer(item).data, status=status.HTTP_201_CREATED
        )


class CartItemDetailView(APIView):
    """PATCH/DELETE /api/cart/items/<id>/ - update or remove one line."""

    permission_classes = [IsAuthenticated]

    def _get_item(self, request, pk):
        # Scoping the lookup to the user's own cart is what prevents cross-user
        # access: a row in someone else's cart simply is not found.
        return CartItem.objects.filter(
            pk=pk, cart__user=request.user
        ).select_related("product", "product__category").first()

    def patch(self, request, pk):
        item = self._get_item(request, pk)
        if item is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartItemSerializer(
            item, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        item = self._get_item(request, pk)
        if item is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    """DELETE /api/cart/clear/ - empty the cart."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
