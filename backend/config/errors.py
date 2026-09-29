"""DRF exception handling.

DRF's default handler echoes `exc.detail` for unhandled exceptions, which for
many exception types includes a traceback. That is unacceptable in production:
it leaks file paths, settings and code structure to callers.

This handler keeps the well-understood, useful messages (validation errors,
404s, permission failures) and replaces everything else with a generic message,
always logging the real detail server-side.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

# Exception types whose message is written for the end user and is safe to
# return. Everything else becomes a generic 500.
SAFE_EXCEPTIONS = (
    exceptions.APIException,
    Http404,
    PermissionDenied,
    DjangoValidationError,
)

GENERIC_DETAIL = "An unexpected error occurred."


def api_exception_handler(exc, context):
    """Return a sanitised response for unhandled API exceptions."""
    response = drf_exception_handler(exc, context)

    if response is not None:
        # A handled exception still deserves a log line for operations.
        logger.warning(
            "API error %s on %s: %s",
            response.status_code,
            _describe(context),
            exc,
        )
        return response

    # Unhandled: log everything, return nothing specific.
    logger.exception("Unhandled API exception on %s", _describe(context))

    from rest_framework import status

    return Response(
        {"detail": GENERIC_DETAIL},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _describe(context):
    """Best-effort description of the request being handled."""
    request = context.get("request") if context else None
    if request is None:
        return "unknown request"
    return f"{request.method} {getattr(request, 'path', '?')}"
