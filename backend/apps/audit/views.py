from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import get_beta_analytics_summary
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

