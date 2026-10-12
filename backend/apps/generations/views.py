from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GenerationJob
from .serializers import APPROVED_MODELS, CreateGenerationJobSerializer, GenerationJobSerializer


class GenerationJobListCreateView(generics.ListCreateAPIView):
    """List synthesis jobs or enqueue a new generation request."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateGenerationJobSerializer
        return GenerationJobSerializer

    def get_queryset(self):
        return GenerationJob.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        # Return full detail serializer representation
        output_serializer = GenerationJobSerializer(job)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class GenerationJobDetailView(generics.RetrieveDestroyAPIView):
    """Poll job status, progress percent, and access generated result audio."""

    serializer_class = GenerationJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return GenerationJob.objects.filter(user=self.request.user)


class ApprovedModelsView(APIView):
    """List approved models satisfying the licensing and benchmark gate (VC-045)."""

    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        models_data = [
            {
                "model_id": "openvoice_v2",
                "name": "OpenVoice V2 ToneColorConverter",
                "license": "MIT",
                "license_status": "VERIFIED",
                "commercial_ready": True,
                "supported_languages": ["en"],
            },
            {
                "model_id": "anadil_uzbek_tts",
                "name": "Anadil Uzbek TTS (VoxCPM2)",
                "license": "MIT / Apache-2.0",
                "license_status": "NEEDS_REVIEW",
                "commercial_ready": False,
                "supported_languages": ["uz"],
            },
            {
                "model_id": "mock_voice_adapter",
                "name": "Development Mock Voice Adapter",
                "license": "MIT",
                "license_status": "VERIFIED",
                "commercial_ready": True,
                "supported_languages": ["uz", "en", "ru"],
            },
        ]
        return Response(
            {"approved_models": [m for m in models_data if m["model_id"] in APPROVED_MODELS]}
        )
