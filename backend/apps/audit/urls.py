from django.urls import path

from .views import (
    AbuseReportDetailView,
    AbuseReportListCreateView,
    AuditEventListView,
    BetaAnalyticsView,
    UnitEconomicsView,
)

app_name = "audit"

urlpatterns = [
    path("reports/", AbuseReportListCreateView.as_view(), name="reports-list-create"),
    path("reports/<uuid:id>/", AbuseReportDetailView.as_view(), name="report-detail"),
    path("events/", AuditEventListView.as_view(), name="events-list"),
    path("analytics/beta/", BetaAnalyticsView.as_view(), name="beta-analytics"),
    path("analytics/economics/", UnitEconomicsView.as_view(), name="unit-economics"),
]
