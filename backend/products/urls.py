"""URL routing for the products API.

Mounted under `/api/` by the project URLconf.
"""

from django.urls import path

from products import views

app_name = "products"

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path(
        "products/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product-detail",
    ),
]
