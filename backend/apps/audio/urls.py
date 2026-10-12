from django.urls import path

from .views import AudioAssetDetailView, AudioAssetListCreateView

app_name = "audio"

urlpatterns = [
    path("", AudioAssetListCreateView.as_view(), name="list-create"),
    path("<uuid:id>/", AudioAssetDetailView.as_view(), name="detail"),
]
