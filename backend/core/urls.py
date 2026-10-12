"""VoiceClone Main URL Routing."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_health(_request):
    """Basic health endpoint for Django API."""
    return JsonResponse({"status": "OK", "service": "voiceclone-backend"})


def api_schema_view(_request):
    """Lightweight OpenAPI specification summary endpoint (VC-047)."""
    return JsonResponse(
        {
            "openapi": "3.1.0",
            "info": {
                "title": "VoiceClone REST API",
                "version": "1.0.0",
                "description": "Ethical, consent-driven speech synthesis and voice cloning API.",
            },
            "paths": {
                "/api/v1/accounts/register/": {"post": {"summary": "Register a new user"}},
                "/api/v1/accounts/me/": {"get": {"summary": "Retrieve authenticated user profile"}},
                "/api/v1/voices/": {
                    "get": {"summary": "List voice profiles"},
                    "post": {"summary": "Create voice profile"},
                },
                "/api/v1/voices/{id}/consent/": {
                    "post": {"summary": "Provide legal voice consent"}
                },
                "/api/v1/audio/": {"post": {"summary": "Upload reference audio asset"}},
                "/api/v1/generations/models/": {
                    "get": {"summary": "List approved models (License Gate)"}
                },
                "/api/v1/generations/jobs/": {
                    "get": {"summary": "List synthesis jobs"},
                    "post": {"summary": "Dispatch speech synthesis job"},
                },
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", api_schema_view, name="api-schema"),
    path("api/v1/health/", api_health, name="api-health"),
    path("api/v1/accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("api/v1/voices/", include("apps.voices.urls", namespace="voices")),
    path("api/v1/audio/", include("apps.audio.urls", namespace="audio")),
    path("api/v1/generations/", include("apps.generations.urls", namespace="generations")),
    path("api/v1/audit/", include("apps.audit.urls", namespace="audit")),
]
