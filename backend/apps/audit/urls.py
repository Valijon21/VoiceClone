from django.urls import path

from .views import AbuseReportDetailView, AbuseReportListCreateView, AuditEventListView

app_name = "audit"

urlpatterns = [
    path("reports/", AbuseReportListCreateView.as_view(), name="reports-list-create"),
    path("reports/<uuid:id>/", AbuseReportDetailView.as_view(), name="report-detail"),
    path("events/", AuditEventListView.as_view(), name="events-list"),
]
