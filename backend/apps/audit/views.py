from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import calculate_unit_economics, get_beta_analytics_summary
from .models import AbuseReport, AuditEvent
from .serializers import AbuseReportSerializer, AuditEventSerializer, CreateAbuseReportSerializer


class AbuseReportListCreateView(generics.ListCreateAPIView):
    """File an abuse or ethics complaint, or view existing reports."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "reports"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAbuseReportSerializer
        return AbuseReportSerializer

    def get_queryset(self):
        # Staff can view all reports, standard users only their own
        if self.request.user.is_staff:
            return AbuseReport.objects.all()
        return AbuseReport.objects.filter(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        # Record audit trail
        AuditEvent.objects.create(
            actor=request.user,
            action=AuditEvent.ACTION_REPORT_SUBMITTED,
            target_model="AbuseReport",
            target_id=str(report.id),
            metadata={
                "reason": report.reason,
                "reported_voice_id": report.reported_voice_id,
                "reported_job_id": report.reported_job_id,
            },
        )

        output_serializer = AbuseReportSerializer(report)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class AbuseReportDetailView(generics.RetrieveUpdateAPIView):
    """View report details or resolve report (Staff only for update)."""

    queryset = AbuseReport.objects.all()
    serializer_class = AbuseReportSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        report = serializer.save()
        if "status" in serializer.validated_data:
            AuditEvent.objects.create(
                actor=self.request.user,
                action=AuditEvent.ACTION_REPORT_RESOLVED,
                target_model="AbuseReport",
                target_id=str(report.id),
                metadata={"status": report.status, "notes": report.resolution_notes},
            )


class AuditEventListView(generics.ListAPIView):
    """List system security and consent audit logs (Admin/Staff only)."""

    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAdminUser]


class BetaAnalyticsView(APIView):
    """
    Beta operational telemetry and performance dashboard (VC-090).
    Aggregates job success rates, latency distributions (p50/p95),
    RTF (Real-Time Factor), model/language breakdown, and error categories.
    Restricted to Admin/Staff users.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        period = request.query_params.get("period", "all")
        if period not in ("24h", "7d", "30d", "all"):
            period = "all"
        data = get_beta_analytics_summary(period=period)
        return Response(data, status=status.HTTP_200_OK)


class UnitEconomicsView(APIView):
    """
    Unit economics, compute COGS, and gross margin dashboard endpoint (VC-094).
    Calculates exact compute cost, storage usage, and margins against commercial tiers.
    Restricted to Admin/Staff users.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        period = request.query_params.get("period", "all")
        if period not in ("24h", "7d", "30d", "all"):
            period = "all"

        try:
            gpu_cost = float(request.query_params.get("gpu_cost", 0.35))
        except (ValueError, TypeError):
            gpu_cost = 0.35

        data = calculate_unit_economics(period=period, gpu_hourly_cost_usd=gpu_cost)
        return Response(data, status=status.HTTP_200_OK)


class TelemetryLogView(APIView):
    """
    Frontend error telemetry ingest endpoint (TASK-LOG-4).
    Receives uncaught browser exceptions, React crash events, and failed API calls,
    routing them into rotating error.log and immutable audit trail.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import logging

        error_logger = logging.getLogger("voiceclone.error")

        data = request.data or {}
        level = data.get("level", "ERROR").upper()
        message = str(data.get("message", "Unknown frontend error"))[:1000]
        url = str(data.get("url", ""))[:255]
        stack = str(data.get("stack", ""))[:2000]
        context = data.get("context", {})

        actor = request.user if request.user and request.user.is_authenticated else None
        user_label = actor.username if actor else "anonymous"

        # Log into rotating error file
        error_logger.error(
            "FRONTEND_TELEMETRY [%s] user=%s url=%s: %s | stack: %s",
            level,
            user_label,
            url,
            message,
            stack.replace("\n", " -> ") if stack else "none",
        )

        # Record in database audit trail for permanent dispute / debug history
        import contextlib

        with contextlib.suppress(Exception):
            AuditEvent.objects.create(
                actor=actor,
                action="FRONTEND_TELEMETRY_ERROR",
                target_model="FrontendTelemetry",
                target_id=url[:64],
                metadata={
                    "level": level,
                    "message": message,
                    "url": url,
                    "stack": stack,
                    "context": context,
                    "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
                },
            )

        return Response({"status": "received"}, status=status.HTTP_202_ACCEPTED)


class SystemLogsView(APIView):
    """
    Protected log viewer and debug dashboard for Platform Owner/Admin (TASK-LOG-5).
    Safely reads tail of rotating log files (app.log, error.log, security.log, inference.log).
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from pathlib import Path

        from django.conf import settings

        log_type = request.query_params.get("type", "app").lower()
        query = request.query_params.get("query", "").lower()
        try:
            lines_count = min(int(request.query_params.get("lines", 50)), 200)
        except (ValueError, TypeError):
            lines_count = 50

        allowed_files = {
            "app": settings.LOG_DIR / "app.log",
            "error": settings.LOG_DIR / "error.log",
            "security": settings.LOG_DIR / "security.log",
            "inference": settings.LOG_DIR / "inference.log",
        }

        target_file: Path = allowed_files.get(log_type, settings.LOG_DIR / "app.log")
        if not target_file.exists():
            return Response(
                {
                    "log_type": log_type,
                    "file_path": str(target_file),
                    "total_returned": 0,
                    "lines": [],
                    "note": "Log file has not been created or written to yet.",
                }
            )

        try:
            with open(target_file, encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()

            # Filter if query provided
            if query:
                all_lines = [ln for ln in all_lines if query in ln.lower()]

            # Tail the requested number of lines
            tail_lines = [ln.rstrip() for ln in all_lines[-lines_count:]]

            return Response(
                {
                    "log_type": log_type,
                    "file_path": target_file.name,
                    "total_returned": len(tail_lines),
                    "lines": tail_lines,
                }
            )
        except Exception as exc:
            return Response(
                {"error": f"Failed to read log file: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


