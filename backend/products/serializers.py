"""Serializers for the read-only catalog API."""

from rest_framework import serializers

from products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Basic category information, used for lists and as a nested field."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class ProductSerializer(serializers.ModelSerializer):
    """Full product representation.

    `category` is expanded to a nested object so clients get the category name
    and slug in the same response. Views pair this with
    `select_related("category")` so the nesting costs no extra queries.
    """

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_active",
            "category",
            "created_at",
            "updated_at",
        ]


class CategoryDetailSerializer(serializers.ModelSerializer):
    """A category together with its active products.

    The view prefetches `products` filtered to active items, so rendering this
    performs a fixed number of queries regardless of how many products a
    category contains.
    """

    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "products"]
