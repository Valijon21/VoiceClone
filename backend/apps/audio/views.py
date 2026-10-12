from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import AudioAsset
from .serializers import AudioAssetSerializer
from .storage import AudioStorageService


class AudioAssetListCreateView(generics.ListCreateAPIView):
    """List audio assets or upload a new audio file."""

    serializer_class = AudioAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return AudioAsset.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error_code": "FILE_REQUIRED", "message": "No audio file was attached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        asset_type = request.data.get("asset_type", AudioAsset.TYPE_REFERENCE)
        audio_bytes = uploaded_file.read()

        asset = AudioStorageService.save_audio_bytes(
            user=request.user,
            filename=uploaded_file.name,
            audio_bytes=audio_bytes,
            duration_sec=3.0,
            sample_rate=24000,
            channels=1,
            asset_type=asset_type,
        )

        serializer = self.get_serializer(asset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AudioAssetDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve metadata or delete an audio asset."""

    serializer_class = AudioAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return AudioAsset.objects.filter(owner=self.request.user)
