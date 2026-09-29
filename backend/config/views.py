"""Infrastructure views that are not tied to a specific application."""

import logging

from django.http import JsonResponse
from django.views.defaults import page_not_found
from django.views.defaults import server_error as server_error_default
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Return a simple liveness payload.

    Deliberately does not touch the database so that it can be used to verify
    that the service is running.
    """
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


def not_found(request, exception):
    """Return JSON 404s for API paths.

    Requests that match no URL pattern never reach a DRF view, so Django would
    otherwise render its HTML error page. API clients expect JSON, so anything
    under /api/ gets a JSON body; other paths keep the default behaviour.
    """
    if not request.path.startswith("/api/"):
        return page_not_found(request, exception)
    return JsonResponse({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


def server_error(request):
    """Return JSON 500s for API paths.

    `handler500` is used for any unhandled exception, including ones raised
    outside a DRF view, so it must never leak a traceback. Django has already
    logged the exception by the time this runs.
    """
    logger.exception("Unhandled server error on %s", request.path)
    if not request.path.startswith("/api/"):
        return server_error_default(request)
    return JsonResponse(
        {"detail": "An unexpected error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
