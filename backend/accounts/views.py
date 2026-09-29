"""Authentication endpoints using Django session cookies.

Session authentication is used rather than a custom token scheme. Django's
`SessionAuthentication` also enforces CSRF on unsafe methods, so no endpoint
here is decorated with `csrf_exempt`.
"""

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.serializers import RegisterSerializer, UserSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    """Issue a CSRF token cookie.

    The browser never talks to Django directly, so this lets the Next.js server
    fetch a token and pass it to the browser, which returns it in the
    `X-CSRFToken` header on unsafe requests.
    """
    return Response({"csrf_token": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Create an account and sign the new user in."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    # Establish a session immediately so the user is signed in after signup.
    login(request, user)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate and start a session.

    The same message is returned for an unknown username and a wrong password
    so the endpoint does not reveal which accounts exist.
    """
    username = request.data.get("username", "")
    password = request.data.get("password", "")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    login(request, user)
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Flush the session and drop the session cookie."""
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the currently authenticated user, or 401 when anonymous."""
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
