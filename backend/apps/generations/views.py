from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GenerationJob
from .serializers import APPROVED_MODELS, CreateGenerationJobSerializer, GenerationJobSerializer


class GenerationJobListCreateView(generics.ListCreateAPIView):
    """List synthesis jobs or enqueue a new generation request."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "generation"

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

        # Dispatch Celery background task (VC-051) with local dev fallback
        if job.status == GenerationJob.STATUS_PENDING:
            dispatched = False
            try:
                from .tasks import process_speech_synthesis_job

                process_speech_synthesis_job.delay(str(job.id))
                dispatched = True
            except Exception:
                pass

            import sys

            if not dispatched and "pytest" not in sys.modules:
                # Local dev fallback: if Celery/Redis broker is unavailable, run in-process
                try:
                    from .tasks import process_speech_synthesis_job

                    process_speech_synthesis_job(str(job.id))
                    job.refresh_from_db()
                except Exception:
                    pass

        output_serializer = GenerationJobSerializer(job)
        headers = {
            "X-AI-Generated": "true",
            "X-VoiceClone-Ethical-Gate": "STRICT",
        }
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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


class RateGenerationJobView(APIView):
    """
    Beta user quality rating and feedback endpoint (VC-091).
    Allows authenticated job owners to provide a 1-5 quality score
    for successful generations.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            job = GenerationJob.objects.select_related("result_audio").get(
                id=id, user=request.user
            )
        except GenerationJob.DoesNotExist:
            return Response(
                {"error_code": "NOT_FOUND", "message": "Job not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if job.status != GenerationJob.STATUS_SUCCEEDED or not hasattr(job, "result_audio"):
            return Response(
                {
                    "error_code": "INVALID_STATE",
                    "message": "Only successfully generated audio can be rated.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating = request.data.get("quality_rating")
        try:
            rating_int = int(rating)
            if not 1 <= rating_int <= 5:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {
                    "error_code": "INVALID_RATING",
                    "message": "quality_rating must be an integer between 1 and 5.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result_audio = job.result_audio
        result_audio.quality_rating = rating_int
        result_audio.save(update_fields=["quality_rating"])

        feedback_notes = request.data.get("feedback_notes", "")
        try:
            from apps.audit.models import AuditEvent

            AuditEvent.objects.create(
                actor=request.user,
                action="AUDIO_QUALITY_RATED",
                target_model="GeneratedAudio",
                target_id=str(result_audio.id),
                metadata={
                    "job_id": str(job.id),
                    "rating": rating_int,
                    "model_id": job.model_id,
                    "language": job.language,
                    "feedback_notes": str(feedback_notes)[:500],
                },
            )
        except Exception:
            pass

        return Response(
            {
                "status": "RATED",
                "job_id": str(job.id),
                "quality_rating": rating_int,
                "feedback_notes": feedback_notes,
            },
            status=status.HTTP_200_OK,
        )
