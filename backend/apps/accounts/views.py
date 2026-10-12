from rest_framework import generics, permissions

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update authenticated user profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LoginView(generics.GenericAPIView):
    """Log in an existing user session."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate, login
        from rest_framework.response import Response

        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response(
                {"detail": "Username and password are required.", "code": "MISSING_CREDENTIALS"},
                status=400,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials provided.", "code": "INVALID_CREDENTIALS"},
                status=401,
            )

        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(generics.GenericAPIView):
    """Log out current user session."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import logout
        from rest_framework.response import Response

        logout(request)
        return Response({"status": "logged_out", "detail": "Session terminated successfully."})


class QuotaStatusView(generics.GenericAPIView):
    """
    Retrieve current quota status, remaining seconds, and recent usage ledger (VC-100).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from rest_framework.response import Response

        from .models import UsageLedger
        from .serializers import UsageLedgerSerializer

        user = request.user
        recent_ledger = UsageLedger.objects.filter(user=user)[:15]

        return Response(
            {
                "user_id": str(user.id),
                "username": user.username,
                "plan": user.plan,
                "is_unlimited": user.is_unlimited,
                "is_owner_or_unlimited": user.is_owner_or_unlimited,
                "audio_seconds_quota": user.audio_seconds_quota,
                "audio_seconds_used": round(user.audio_seconds_used, 2),
                "remaining_seconds": user.remaining_seconds,
                "recent_ledger": UsageLedgerSerializer(recent_ledger, many=True).data,
            }
        )


class AdminUserPlanUpdateView(generics.GenericAPIView):
    """
    Owner/Admin endpoint to grant unlimited access, upgrade plans, or adjust quota (VC-100).
    Allows system owner to grant VIP/unlimited access to any user or friend.
    """

    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404
        from rest_framework.response import Response

        from .models import UsageLedger
        from .serializers import AdminPlanUpdateSerializer

        target_user = get_object_or_404(User, pk=pk)
        serializer = AdminPlanUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        old_plan = target_user.plan
        old_unlimited = target_user.is_unlimited
        note = data.get("note", f"Admin override by {request.user.username}")

        delta = 0.0
        if "plan" in data:
            target_user.plan = data["plan"]
            if data["plan"] == User.PLAN_UNLIMITED:
                target_user.is_unlimited = True

        if "is_unlimited" in data:
            target_user.is_unlimited = data["is_unlimited"]

        if "audio_seconds_quota" in data:
            delta = float(data["audio_seconds_quota"]) - float(target_user.audio_seconds_quota)
            target_user.audio_seconds_quota = data["audio_seconds_quota"]

        if "bonus_seconds" in data:
            bonus = float(data["bonus_seconds"])
            target_user.audio_seconds_quota += int(bonus)
            delta += bonus

        target_user.save()

        # Immutable ledger audit trail
        UsageLedger.objects.create(
            user=target_user,
            operation=UsageLedger.OPERATION_OVERRIDE,
            delta_seconds=delta,
            balance_after_seconds=target_user.remaining_seconds,
            notes=(
                f"{note} (plan: {old_plan}->{target_user.plan}, "
                f"unlimited: {old_unlimited}->{target_user.is_unlimited})"
            ),
        )

        return Response(
            {
                "status": "success",
                "detail": f"User {target_user.username} plan/quota updated successfully.",
                "user": UserSerializer(target_user).data,
            }
        )


class AdminUserListView(generics.ListAPIView):
    """Owner/Admin endpoint to list all users and their quota/unlimited status."""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by("-created_at")
