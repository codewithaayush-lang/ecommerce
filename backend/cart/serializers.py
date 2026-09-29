"""Cart serializers.

All monetary values are calculated on the server from the live Product price.
The client never sends a price or a total, and none is persisted.
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from cart.models import Cart, CartItem
from products.serializers import CategorySerializer
from products.models import Product

ZERO = Decimal("0.00")


class ProductSummarySerializer(serializers.ModelSerializer):
    """Compact product payload embedded in cart lines."""

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "stock", "is_active", "category"]


class CartItemSerializer(serializers.ModelSerializer):
    """A cart line with its calculated line total."""

    id = serializers.IntegerField(read_only=True)
    product = ProductSummarySerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(is_active=True),
        write_only=True,
    )
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="product.price"
    )
    line_total = serializers.SerializerMethodField()
    # Exceeding available stock is a validation concern, not a stock deduction.
    max_quantity = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
            "max_quantity",
        ]
        read_only_fields = ["id", "product", "unit_price", "line_total", "max_quantity"]

    def get_line_total(self, obj):
        return str(obj.line_total)

    def get_max_quantity(self, obj):
        """How many more units of this product the store can currently supply."""
        return max(obj.product.stock - obj.quantity, 0)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate(self, attrs):
        """Check the requested quantity against current stock.

        On a PATCH only `quantity` is supplied, so the product and the existing
        quantity must be read from the instance being updated. Without this
        fallback a PATCH would skip the stock check entirely.
        """
        product = attrs.get("product")
        if product is None and self.instance is not None:
            product = self.instance.product

        if product is None:
            return attrs

        quantity = attrs.get("quantity")
        if quantity is None:
            quantity = self.instance.quantity if self.instance is not None else 1

        if not product.is_active:
            raise serializers.ValidationError("This product is not available.")

        if quantity > product.stock:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        f"Only {product.stock} of this product "
                        f"{'is' if product.stock == 1 else 'are'} in stock."
                    )
                }
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """The cart with its lines, calculated subtotal and unit count."""

    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "subtotal", "item_count", "currency", "updated_at"]
        read_only_fields = fields

    def _lines(self, cart):
        """Prefer prefetched items to avoid a per-object query."""
        prefetched = getattr(cart, "_prefetched_objects_cache", None)
        if prefetched and "items" in prefetched:
            return list(prefetched["items"])
        return list(cart.items.all())

    def get_subtotal(self, cart):
        # Derived from the item serializer's line totals, which come from the
        # live Product price.
        total = sum(
            (Decimal(item.product.price) * item.quantity for item in self._lines(cart)),
            ZERO,
        )
        return str(total)

    def get_item_count(self, cart):
        return sum(item.quantity for item in self._lines(cart))

    def get_currency(self, cart):
        # Prices are stored without a currency; formatting happens downstream.
        return "USD"
