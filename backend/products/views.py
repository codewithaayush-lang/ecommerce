"""Read-only catalog API views.

The catalog is public: no authentication or permissions are configured, and
only list/retrieve endpoints are provided.
"""

from django.db.models import Prefetch
from rest_framework import generics
from rest_framework.filters import SearchFilter

from products.models import Category, Product
from products.serializers import (
    CategoryDetailSerializer,
    CategorySerializer,
    ProductSerializer,
)


class CategoryListView(generics.ListAPIView):
    """List every category.

    Categories are a small, bounded set that clients use to build filters and
    navigation, so this endpoint returns a plain list rather than a paginated
    envelope. Product listings are paginated instead.
    """

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = None


class CategoryDetailView(generics.RetrieveAPIView):
    """Retrieve one category by slug, including its active products."""

    serializer_class = CategoryDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        active_products = Product.objects.filter(is_active=True).select_related(
            "category"
        )
        return Category.objects.prefetch_related(
            Prefetch("products", queryset=active_products)
        )


class ProductListView(generics.ListAPIView):
    """List active products, with optional search, category filter, paging.

    Query parameters:
        ?search=<term>     matches product name or description
        ?category=<slug>   restricts results to one category
        ?page=<number>     page number, using DRF page number pagination
    """

    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name", "description"]

    def get_queryset(self):
        # Inactive products are never publicly listed.
        queryset = Product.objects.filter(is_active=True).select_related("category")

        category_slug = self.request.query_params.get("category")
        if category_slug:
            # An unknown category slug yields an empty list rather than an error.
            queryset = queryset.filter(category__slug=category_slug)

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """Retrieve one active product by slug.

    Inactive products are excluded from the queryset, so DRF returns 404 for
    them instead of leaking their existence.
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True).select_related("category")
    lookup_field = "slug"
