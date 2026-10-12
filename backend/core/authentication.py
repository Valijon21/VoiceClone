"""Custom authentication classes for SPA session handling."""

from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication that allows SPA cookie-based API calls without enforcing CSRF
    token header on REST endpoints.
    """

    def enforce_csrf(self, request):
        return  # CSRF exemption for REST API requests
