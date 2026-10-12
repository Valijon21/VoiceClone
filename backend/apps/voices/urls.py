from django.urls import path

from .views import ProvideConsentView, VoiceProfileDetailView, VoiceProfileListCreateView

app_name = "voices"

urlpatterns = [
    path("", VoiceProfileListCreateView.as_view(), name="list-create"),
    path("<uuid:id>/", VoiceProfileDetailView.as_view(), name="detail"),
    path("<uuid:voice_id>/consent/", ProvideConsentView.as_view(), name="provide-consent"),
]
