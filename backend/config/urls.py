"""Root URL configuration.

All API endpoints are namespaced under `/api/`.
"""

from django.urls import include, path

from config import views

urlpatterns = [
    path("api/health/", views.health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("orders.urls")),
]

# Error responses are JSON for API paths, HTML elsewhere.
handler404 = "config.views.not_found"
handler500 = "config.views.server_error"
