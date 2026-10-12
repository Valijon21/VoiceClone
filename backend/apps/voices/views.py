from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import ConsentRecord, VoiceProfile
from .permissions import IsVoiceOwner
from .serializers import ConsentRecordSerializer, VoiceProfileSerializer


class VoiceProfileListCreateView(generics.ListCreateAPIView):
    """List or create voice profiles belonging to authenticated user."""

    serializer_class = VoiceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VoiceProfile.objects.filter(owner=self.request.user)


class VoiceProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a voice profile."""

    serializer_class = VoiceProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsVoiceOwner]
    lookup_field = "id"

    def get_queryset(self):
        return VoiceProfile.objects.filter(owner=self.request.user)


class ProvideConsentView(generics.CreateAPIView):
    """Record verified legal consent for a voice profile."""

    serializer_class = ConsentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        voice_id = self.kwargs.get("voice_id")
        voice_profile = generics.get_object_or_404(
            VoiceProfile,
            id=voice_id,
            owner=request.user,
        )

        consent_text = request.data.get(
            "consent_text",
            "Men ushbu ovoz mening shaxsiy ovozim ekanini yoki undan foydalanishga to‘liq huquqim borligini tasdiqlayman.",
        )

        consent, _created = ConsentRecord.objects.update_or_create(
            voice_profile=voice_profile,
            defaults={
                "user": request.user,
                "consent_text": consent_text,
                "status": ConsentRecord.STATUS_VERIFIED,
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
                "revoked_at": None,
            },
        )

        serializer = self.get_serializer(consent)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
