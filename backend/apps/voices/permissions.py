"""Custom object and action permissions for Voice Profiles and Consent."""

from rest_framework import permissions


class IsVoiceOwner(permissions.BasePermission):
    """Allow access only to the owner of the voice profile."""

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user


class HasVerifiedConsent(permissions.BasePermission):
    """Enforce the Consent Gate: Disallow synthesizing or using any unverified voice."""

    message = "Voice profile cannot be used without a valid, verified consent record."

    def has_object_permission(self, request, view, obj):
        # obj is VoiceProfile
        return getattr(obj, "has_verified_consent", False)
