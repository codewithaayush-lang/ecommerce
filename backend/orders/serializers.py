"""Order serializers.

Order history is rendered entirely from the snapshot fields on OrderItem, so
an order's contents never change when a Product is later edited or repriced.
"""

from rest_framework import serializers

from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """A purchased line, shown from its snapshot values."""

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "line_total",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Full order representation used for the detail endpoint."""

    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "subtotal",
            "total",
            "currency",
            "item_count",
            "can_cancel",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_currency(self, obj):
        # Prices are stored without a currency; the client formats them.
        return "USD"


class OrderListSerializer(serializers.ModelSerializer):
    """Compact order representation used for the history list."""

    item_count = serializers.IntegerField(read_only=True)
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "total",
            "currency",
            "item_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_currency(self, obj):
        return "USD"
