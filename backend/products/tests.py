"""Tests for the products app.

All test data is created inside the temporary test database that Django builds
and tears down, so the development database is never touched.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product


class ProductAPITestCase(TestCase):
    """Shared fixtures for the catalog API tests."""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        cls.kitchen = Category.objects.create(
            name="Kitchen",
            slug="kitchen",
            description="Cooking equipment",
        )
        cls.lighting = Category.objects.create(
            name="Lighting",
            slug="lighting",
            description="Lamps and shades",
        )

        cls.kettle = Product.objects.create(
            name="Copper Kettle",
            slug="copper-kettle",
            description="A stovetop kettle for everyday use.",
            price=Decimal("49.90"),
            category=cls.kitchen,
            stock=12,
        )
        cls.bowl = Product.objects.create(
            name="Stoneware Bowl",
            slug="stoneware-bowl",
            description="A sturdy bowl for serving.",
            price=Decimal("18.00"),
            category=cls.kitchen,
            stock=4,
        )
        cls.lamp = Product.objects.create(
            name="Desk Lamp",
            slug="desk-lamp",
            description="Adjustable lamp for a desk.",
            price=Decimal("35.50"),
            category=cls.lighting,
            stock=7,
        )
        cls.retired = Product.objects.create(
            name="Retired Kettle",
            slug="retired-kettle",
            description="Discontinued, must not be public.",
            price=Decimal("59.00"),
            category=cls.kitchen,
            stock=0,
            is_active=False,
        )


class CategoryListTests(ProductAPITestCase):
    def test_returns_all_categories(self):
        response = self.client.get(reverse("products:category-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [item["slug"] for item in response.data]
        self.assertEqual(slugs, ["kitchen", "lighting"])

    def test_exposes_expected_fields_only(self):
        response = self.client.get(reverse("products:category-list"))

        self.assertEqual(
            set(response.data[0].keys()),
            {"id", "name", "slug", "description"},
        )

    def test_is_not_paginated(self):
        # Categories are small and bounded, so this endpoint returns a plain
        # list instead of a paginated envelope.
        response = self.client.get(reverse("products:category-list"))

        self.assertIsInstance(response.data, list)


class CategoryDetailTests(ProductAPITestCase):
    def test_returns_category_by_slug(self):
        response = self.client.get(
            reverse("products:category-detail", args=["kitchen"])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "kitchen")
        self.assertEqual(response.data["name"], "Kitchen")

    def test_includes_only_active_products(self):
        response = self.client.get(
            reverse("products:category-detail", args=["kitchen"])
        )

        slugs = [item["slug"] for item in response.data["products"]]
        self.assertIn("copper-kettle", slugs)
        self.assertIn("stoneware-bowl", slugs)
        self.assertNotIn("retired-kettle", slugs)

    def test_nested_products_expose_full_product_fields(self):
        response = self.client.get(
            reverse("products:category-detail", args=["lighting"])
        )

        product = response.data["products"][0]
        self.assertEqual(
            set(product.keys()),
            {
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
            },
        )

    def test_nonexistent_category_returns_404(self):
        response = self.client.get(
            reverse("products:category-detail", args=["does-not-exist"])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_does_not_cause_n_plus_one_queries(self):
        for index in range(10):
            Product.objects.create(
                name=f"Detail Item {index:02d}",
                slug=f"detail-item-{index:02d}",
                description="Padding for the detail query count test.",
                price=Decimal("4.00"),
                category=self.kitchen,
                stock=1,
            )

        with self.assertNumQueries(2):
            # One query for the category, one prefetch for its active products
            # (each already carrying its category, so no per-product queries).
            response = self.client.get(
                reverse("products:category-detail", args=["kitchen"])
            )
            self.assertEqual(response.data["slug"], "kitchen")
            self.assertEqual(len(response.data["products"]), 12)
            for product in response.data["products"]:
                self.assertIn("slug", product["category"])


class ProductListTests(ProductAPITestCase):
    def test_returns_only_active_products(self):
        response = self.client.get(reverse("products:product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(
            sorted(slugs), ["copper-kettle", "desk-lamp", "stoneware-bowl"]
        )
        self.assertNotIn("retired-kettle", slugs)

    def test_exposes_expected_fields_only(self):
        response = self.client.get(reverse("products:product-list"))

        self.assertEqual(
            set(response.data["results"][0].keys()),
            {
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
            },
        )

    def test_includes_nested_category(self):
        response = self.client.get(reverse("products:product-list"))

        product = response.data["results"][0]
        self.assertEqual(
            set(product["category"].keys()),
            {"id", "name", "slug", "description"},
        )

    def test_search_matches_name(self):
        response = self.client.get(
            reverse("products:product-list"), {"search": "kettle"}
        )

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["copper-kettle"])

    def test_search_matches_description(self):
        response = self.client.get(
            reverse("products:product-list"), {"search": "serving"}
        )

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["stoneware-bowl"])

    def test_search_is_case_insensitive(self):
        response = self.client.get(
            reverse("products:product-list"), {"search": "DESK LAMP"}
        )

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["desk-lamp"])

    def test_search_excludes_inactive_products(self):
        response = self.client.get(
            reverse("products:product-list"), {"search": "retired"}
        )

        self.assertEqual(response.data["count"], 0)

    def test_search_with_no_matches_returns_empty_page(self):
        response = self.client.get(
            reverse("products:product-list"), {"search": "zzzznomatch"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_by_category_slug(self):
        response = self.client.get(
            reverse("products:product-list"), {"category": "lighting"}
        )

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["desk-lamp"])

    def test_filter_by_category_excludes_inactive(self):
        response = self.client.get(
            reverse("products:product-list"), {"category": "kitchen"}
        )

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(sorted(slugs), ["copper-kettle", "stoneware-bowl"])

    def test_filter_by_unknown_category_returns_empty_list(self):
        response = self.client.get(
            reverse("products:product-list"), {"category": "no-such-category"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_filter_by_blank_category_is_ignored(self):
        response = self.client.get(
            reverse("products:product-list"), {"category": ""}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_search_and_category_filter_combine(self):
        response = self.client.get(
            reverse("products:product-list"),
            {"search": "kettle", "category": "lighting"},
        )

        self.assertEqual(response.data["count"], 0)

    def test_is_paginated_with_default_page_size(self):
        response = self.client.get(reverse("products:product-list"))

        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_pagination_splits_results(self):
        for index in range(15):
            Product.objects.create(
                name=f"Bulk Item {index:02d}",
                slug=f"bulk-item-{index:02d}",
                description="Padding for the pagination test.",
                price=Decimal("1.00"),
                category=self.lighting,
                stock=1,
            )

        first = self.client.get(reverse("products:product-list"))
        self.assertEqual(first.data["count"], 18)
        self.assertEqual(len(first.data["results"]), 12)
        self.assertIsNotNone(first.data["next"])
        self.assertIsNone(first.data["previous"])

        second = self.client.get(
            reverse("products:product-list"), {"page": 2}
        )
        self.assertEqual(len(second.data["results"]), 6)
        self.assertIsNone(second.data["next"])
        self.assertIsNotNone(second.data["previous"])

    def test_invalid_page_number_is_handled(self):
        response = self.client.get(
            reverse("products:product-list"), {"page": "not-a-number"}
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST],
        )
        self.assertIn("detail", response.data)

    def test_out_of_range_page_is_handled(self):
        response = self.client.get(
            reverse("products:product-list"), {"page": 999}
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST],
        )

    def test_unknown_query_parameters_are_ignored(self):
        response = self.client.get(
            reverse("products:product-list"), {"nonsense": "value"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_nested_category_does_not_cause_n_plus_one_queries(self):
        for index in range(8):
            Product.objects.create(
                name=f"Query Item {index:02d}",
                slug=f"query-item-{index:02d}",
                description="Padding for the query count test.",
                price=Decimal("2.00"),
                category=self.lighting,
                stock=1,
            )

        with self.assertNumQueries(2):
            # One COUNT query for pagination plus one for the page of rows.
            # If nested categories were lazy-loaded this would grow per row.
            response = self.client.get(reverse("products:product-list"))
            self.assertEqual(response.data["count"], 11)
            self.assertEqual(len(response.data["results"]), 11)
            for item in response.data["results"]:
                self.assertIn("slug", item["category"])

    def test_number_of_queries_is_independent_of_result_count(self):
        url = reverse("products:product-list")
        with self.assertNumQueries(2):
            self.client.get(url)

        for index in range(10):
            Product.objects.create(
                name=f"Scale Item {index:02d}",
                slug=f"scale-item-{index:02d}",
                description="Padding for the query scaling test.",
                price=Decimal("3.00"),
                category=self.kitchen,
                stock=1,
            )

        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.data["count"], 13)


class ProductDetailTests(ProductAPITestCase):
    def test_returns_active_product_by_slug(self):
        response = self.client.get(
            reverse("products:product-detail", args=["copper-kettle"])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "copper-kettle")
        self.assertEqual(response.data["price"], "49.90")
        self.assertEqual(response.data["category"]["slug"], "kitchen")

    def test_nonexistent_product_returns_404(self):
        response = self.client.get(
            reverse("products:product-detail", args=["no-such-product"])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_product_is_not_accessible(self):
        response = self.client.get(
            reverse("products:product-detail", args=["retired-kettle"])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_category_slug_does_not_expose_inactive_product(self):
        # The retired product is filtered out of the queryset, so the detail
        # endpoint cannot be used to discover it by guessing slugs.
        response = self.client.get(
            reverse("products:product-detail", args=["retired-kettle"])
        )

        self.assertNotIn("price", response.data)


class HealthEndpointTests(TestCase):
    """The pre-existing health endpoint must keep working unchanged."""

    def test_health_still_returns_ok(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})


class NotFoundHandlerTests(TestCase):
    """Unmatched API paths must return JSON, not Django's HTML error page."""

    def test_unknown_api_path_returns_json(self):
        response = self.client.get("/api/nope/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_malformed_slug_returns_json(self):
        response = self.client.get("/api/products/not a slug/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_non_api_path_keeps_default_handler(self):
        response = self.client.get("/not-an-api-path/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("text/html", response["Content-Type"])
