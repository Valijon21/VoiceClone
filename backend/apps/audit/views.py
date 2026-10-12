from rest_framework import generics, permissions, status
from rest_framework.response import Response

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
