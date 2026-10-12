from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import AudioAsset
from .serializers import AudioAssetSerializer
from .storage import AudioStorageService

ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
}
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_FILE_SIZE_BYTES = 44  # Minimum valid audio container size
USER_STORAGE_QUOTA_BYTES = 100 * 1024 * 1024  # 100 MB per user


class AudioAssetListCreateView(generics.ListCreateAPIView):
    """List audio assets or upload a new audio file."""

    serializer_class = AudioAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "audio_upload"

    def get_queryset(self):
        return AudioAsset.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error_code": "FILE_REQUIRED", "message": "No audio file was attached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. File size checks
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            return Response(
                {
                    "error_code": "FILE_TOO_LARGE",
                    "message": f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        if uploaded_file.size < MIN_FILE_SIZE_BYTES:
            return Response(
                {
                    "error_code": "MALFORMED_AUDIO_FILE",
                    "message": "File is too small to be a valid audio stream.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Extension & MIME validation
        filename_lower = uploaded_file.name.lower()
        has_valid_ext = any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        content_type = getattr(uploaded_file, "content_type", "").lower()

        if not has_valid_ext and content_type not in ALLOWED_MIME_TYPES:
            return Response(
                {
                    "error_code": "UNSUPPORTED_MEDIA_TYPE",
                    "message": "Unsupported file format. Only WAV, MP3, OGG, and M4A are supported.",
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # 3. User quota validation
        user_total_bytes = sum(
            asset.size_bytes for asset in AudioAsset.objects.filter(owner=request.user)
        )
        if user_total_bytes + uploaded_file.size > USER_STORAGE_QUOTA_BYTES:
            return Response(
                {
                    "error_code": "STORAGE_QUOTA_EXCEEDED",
                    "message": "User storage quota of 100 MB exceeded. Please delete old assets.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Binary header verification for WAV
        audio_bytes = uploaded_file.read()
        if (filename_lower.endswith(".wav") or "wav" in content_type) and (
            len(audio_bytes) < 44 or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE"
        ):
            return Response(
                {
                    "error_code": "MALFORMED_AUDIO_FILE",
                    "message": "Malformed WAV header. Expected valid RIFF/WAVE signature.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        asset_type = request.data.get("asset_type", AudioAsset.TYPE_REFERENCE)

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
