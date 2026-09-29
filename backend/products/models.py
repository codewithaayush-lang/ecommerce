"""Database models for the product catalog.

These models hold catalog data only. There is no image handling, cart, order,
or payment behaviour here; those belong to later steps.
"""

from django.db import models


class Category(models.Model):
    """A group that products belong to, e.g. "Kitchen" or "Lighting"."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """A single item that can be listed and purchased."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "products"
        indexes = [
            # Supports catalog listings that filter to active products within
            # a single category. The foreign key is already indexed on its own.
            models.Index(
                fields=["is_active", "category"],
                name="products_active_category_idx",
            ),
        ]

    def __str__(self):
        return self.name
