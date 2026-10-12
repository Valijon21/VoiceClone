"""Tests for structured rotating file logging, end-to-end correlation tracing, and telemetry (TASK-LOG-6)."""

import pytest
from apps.accounts.models import User
from apps.audit.models import AuditEvent
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_user(db):
    return User.objects.create_user(
        username="logging_test_user",
        email="logging_user@voiceclone.local",
        password="ValidPassword123!",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="logging_admin_user",
        email="logging_admin@voiceclone.local",
        password="AdminPassword123!",
    )


@pytest.mark.django_db
def test_correlation_id_generated_and_returned(api_client):
    """Verify that every HTTP response includes an X-Request-ID header."""
    resp = api_client.get("/api/v1/health/")
    assert resp.status_code == status.HTTP_200_OK
    assert "X-Request-ID" in resp.headers
    req_id = resp.headers["X-Request-ID"]
    assert req_id.startswith("req_")


@pytest.mark.django_db
def test_correlation_id_propagated_from_client(api_client):
    """Verify that client-supplied X-Request-ID is preserved and echoed in response."""
    custom_trace = "fe_trace_test_998877"
    resp = api_client.get("/api/v1/health/", HTTP_X_REQUEST_ID=custom_trace)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers.get("X-Request-ID") == custom_trace


@pytest.mark.django_db
def test_app_log_file_written(api_client):
    """Verify that HTTP requests write structured log entries into app.log."""
    app_log = settings.LOG_DIR / "app.log"
    custom_trace = "trace_app_log_verify_123"

    api_client.get("/api/v1/health/", HTTP_X_REQUEST_ID=custom_trace)

    assert app_log.exists()
    content = app_log.read_text(encoding="utf-8", errors="replace")
    assert custom_trace in content
    assert "GET /api/v1/health/" in content


@pytest.mark.django_db
def test_security_log_records_unauthorized_access(api_client):
    """Verify that 401/403 access rejections are captured in security.log."""
    sec_log = settings.LOG_DIR / "security.log"
    custom_trace = "sec_trace_unauth_401"

    # Access protected endpoint without auth -> 401 or 403
    resp = api_client.get("/api/v1/accounts/me/", HTTP_X_REQUEST_ID=custom_trace)
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    assert sec_log.exists()
    content = sec_log.read_text(encoding="utf-8", errors="replace")
    assert custom_trace in content
    assert "ACCESS_DENIED" in content


@pytest.mark.django_db
def test_frontend_telemetry_endpoint_records_error_and_audit(api_client, standard_user):
    """Verify that browser runtime exceptions are recorded into error.log and AuditEvent."""
    api_client.force_authenticate(user=standard_user)
    error_log = settings.LOG_DIR / "error.log"

    payload = {
        "level": "ERROR",
        "message": "Uncaught TypeError: Cannot read property 'map' of undefined",
        "url": "http://localhost:5173/voices",
        "stack": "TypeError at VoicesList.tsx:42 -> renderApp.tsx:12",
        "context": {"component": "VoicesList", "action": "render"},
    }

    resp = api_client.post("/api/v1/audit/telemetry/", payload, format="json")
    assert resp.status_code == status.HTTP_202_ACCEPTED
    assert resp.json()["status"] == "received"

    # 1. Check database audit event
    audit = AuditEvent.objects.filter(action="FRONTEND_TELEMETRY_ERROR").first()
    assert audit is not None
    assert audit.actor == standard_user
    assert "Cannot read property 'map'" in audit.metadata["message"]

    # 2. Check error.log file
    assert error_log.exists()
    content = error_log.read_text(encoding="utf-8", errors="replace")
    assert "FRONTEND_TELEMETRY" in content
    assert "Cannot read property 'map'" in content


@pytest.mark.django_db
def test_admin_system_logs_view_permissions_and_tail(api_client, standard_user, admin_user):
    """Verify that only admin users can inspect rotating system logs via the API."""
    logs_url = "/api/v1/audit/logs/?type=app&lines=20"

    # Standard user receives 403 Forbidden
    api_client.force_authenticate(user=standard_user)
    resp_user = api_client.get(logs_url)
    assert resp_user.status_code == status.HTTP_403_FORBIDDEN

    # Admin user receives 200 OK with log lines array
    api_client.force_authenticate(user=admin_user)
    resp_admin = api_client.get(logs_url)
    assert resp_admin.status_code == status.HTTP_200_OK
    data = resp_admin.json()
    assert "log_type" in data
    assert data["log_type"] == "app"
    assert "lines" in data
    assert isinstance(data["lines"], list)
