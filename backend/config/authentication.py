"""Authentication classes shared by the API."""

from rest_framework.authentication import SessionAuthentication


class SessionAuthenticationWith401(SessionAuthentication):
    """Session authentication that answers 401 instead of 403.

    DRF returns 401 only when the first authenticator provides a
    `WWW-Authenticate` header. DRF's `SessionAuthentication` deliberately does
    not, so unauthenticated requests fall through to a bare 403. Overriding
    `authenticate_header` makes unauthenticated access to protected endpoints
    report 401, which is the correct status for "you are not signed in".

    CSRF behaviour is unchanged: `authenticate()` still enforces the CSRF check
    for unsafe methods, so this is not a way around CSRF protection.
    """

    def authenticate_header(self, request):
        return 'Session realm="api"'
