"""URL routing for the cart. Mounted under /api/."""

from django.urls import path

from cart import views

app_name = "cart"

urlpatterns = [
    path("cart/", views.CartDetailView.as_view(), name="cart-detail"),
    path("cart/items/", views.CartItemListView.as_view(), name="cart-item-list"),
    path(
        "cart/items/<int:pk>/",
        views.CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path("cart/clear/", views.CartClearView.as_view(), name="cart-clear"),
]
