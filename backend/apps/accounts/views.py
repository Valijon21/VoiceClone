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


class SubscriptionDetailView(generics.GenericAPIView):
    """
    Retrieve current subscription status or activate/upgrade a subscription (VC-102).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from rest_framework.response import Response

        from .models import Subscription
        from .serializers import SubscriptionSerializer

        user = request.user
        sub = (
            Subscription.objects.filter(user=user)
            .exclude(status__in=[Subscription.STATUS_EXPIRED, Subscription.STATUS_CANCELED])
            .first()
        )
        if sub:
            return Response(SubscriptionSerializer(sub).data)

        # Default free trial representation
        return Response(
            {
                "id": None,
                "plan": user.plan,
                "status": "FREE_TRIAL",
                "billing_cycle": "MONTHLY",
                "price_amount": "0.00",
                "currency": "UZS",
                "current_period_start": user.created_at,
                "current_period_end": None,
                "cancel_at_period_end": False,
                "grace_period_until": None,
                "failed_payment_count": 0,
                "is_active_or_in_grace": True,
                "transactions": [],
            }
        )

    def post(self, request):
        from rest_framework.response import Response

        from .serializers import SubscriptionCreateSerializer, SubscriptionSerializer
        from .services import SubscriptionLifecycleService

        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sub, tx = SubscriptionLifecycleService.activate_subscription(
            user=request.user,
            plan=data["plan"],
            billing_cycle=data.get("billing_cycle", "MONTHLY"),
            provider=data.get("provider", "MOCK"),
            provider_transaction_id=data.get("provider_transaction_id"),
            idempotency_key=data.get("idempotency_key"),
        )
        return Response(
            {
                "status": "success",
                "message": f"Successfully subscribed to {sub.plan} tier.",
                "subscription": SubscriptionSerializer(sub).data,
                "transaction_id": str(tx.id),
            },
            status=201,
        )


class SubscriptionCancelView(generics.GenericAPIView):
    """
    Cancel an active subscription at period end or immediately (VC-102).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from rest_framework.response import Response

        from .models import Subscription
        from .serializers import SubscriptionCancelSerializer, SubscriptionSerializer
        from .services import SubscriptionLifecycleService

        serializer = SubscriptionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sub = (
            Subscription.objects.filter(user=request.user)
            .exclude(status__in=[Subscription.STATUS_EXPIRED, Subscription.STATUS_CANCELED])
            .first()
        )
        if not sub:
            return Response({"detail": "No active subscription found to cancel."}, status=404)

        sub = SubscriptionLifecycleService.cancel_subscription(
            subscription=sub,
            immediate=data.get("immediate", False),
            reason=data.get("reason", "User requested cancel"),
        )
        return Response(
            {
                "status": "success",
                "message": "Subscription canceled successfully.",
                "subscription": SubscriptionSerializer(sub).data,
            }
        )


class PaymentTransactionListView(generics.ListAPIView):
    """
    List user's payment and refund transaction history (VC-102).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import PaymentTransactionSerializer

        return PaymentTransactionSerializer

    def get_queryset(self):
        from .models import PaymentTransaction

        return PaymentTransaction.objects.filter(user=self.request.user).order_by("-created_at")


class AdminRefundProcessView(generics.GenericAPIView):
    """
    Admin-only endpoint to issue refunds and safely rollback quota (VC-102).
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from django.shortcuts import get_object_or_404
        from rest_framework.response import Response

        from .models import PaymentTransaction
        from .serializers import PaymentTransactionSerializer, RefundRequestSerializer
        from .services import SubscriptionLifecycleService

        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tx = get_object_or_404(PaymentTransaction, id=data["transaction_id"])
        try:
            tx = SubscriptionLifecycleService.process_refund(
                transaction_obj=tx,
                refund_amount=data.get("refund_amount"),
                reason=data.get("reason", "Admin issued refund"),
            )
        except ValueError as err:
            return Response({"detail": str(err)}, status=400)

        return Response(
            {
                "status": "success",
                "message": "Refund processed successfully.",
                "transaction": PaymentTransactionSerializer(tx).data,
            }
        )


class SimulatePaymentFailureView(generics.GenericAPIView):
    """
    Simulate recurring payment failure / card decline to verify quota invariants (VC-102).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from rest_framework.response import Response

        from .models import Subscription
        from .serializers import PaymentTransactionSerializer
        from .services import SubscriptionLifecycleService

        sub = (
            Subscription.objects.filter(user=request.user)
            .exclude(status__in=[Subscription.STATUS_EXPIRED, Subscription.STATUS_CANCELED])
            .first()
        )
        if not sub:
            return Response({"detail": "No active subscription found for test."}, status=404)

        reason = request.data.get("reason", "Card charge declined by issuing bank")
        code = request.data.get("code", "INSUFFICIENT_FUNDS")

        fail_tx = SubscriptionLifecycleService.handle_payment_failure(
            subscription=sub,
            failure_reason=reason,
            failure_code=code,
        )
        return Response(
            {
                "status": "failure_simulated",
                "detail": "Payment failure handled. Quota remains uncorrupted.",
                "subscription_status": sub.status,
                "grace_period_until": sub.grace_period_until,
                "transaction": PaymentTransactionSerializer(fail_tx).data,
            }
        )


class CheckoutInitiateView(generics.GenericAPIView):
    """
    Generate payment checkout link for Payme or Click (VC-101).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from decimal import Decimal

        from rest_framework.response import Response

        from .gateways import ClickGateway, PaymeGateway
        from .models import Subscription
        from .serializers import CheckoutInitiateSerializer

        serializer = CheckoutInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = data["plan"]
        cycle = data.get("billing_cycle", "MONTHLY")
        provider = data.get("provider", "PAYME")
        return_url = data.get("return_url")

        base_price = Decimal(str(Subscription.PLAN_PRICES_UZS.get(plan, 79000.0)))
        amount = base_price * Decimal("10.0") if cycle == Subscription.CYCLE_YEARLY else base_price

        if provider == "PAYME":
            gateway = PaymeGateway()
            checkout_url = gateway.generate_payment_link(
                user=request.user,
                plan=plan,
                amount=amount,
                billing_cycle=cycle,
                return_url=return_url,
            )
        elif provider == "CLICK":
            gateway = ClickGateway()
            checkout_url = gateway.generate_payment_link(
                user=request.user,
                plan=plan,
                amount=amount,
                billing_cycle=cycle,
                return_url=return_url,
            )
        else:
            return Response(
                {"detail": f"Provider {provider} not supported for checkout."}, status=400
            )

        return Response(
            {
                "status": "success",
                "provider": provider,
                "plan": plan,
                "billing_cycle": cycle,
                "amount": amount,
                "currency": "UZS",
                "payment_url": checkout_url,
            }
        )


class PaymeWebhookView(generics.GenericAPIView):
    """
    Payme JSON-RPC 2.0 Webhook Endpoint (VC-101).
    Public endpoint verified via HTTP Basic Authentication.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from rest_framework.response import Response

        from .gateways import PaymeGateway

        gateway = PaymeGateway()
        response_payload = gateway.process_webhook(request.data, request.headers)
        return Response(response_payload)


class ClickWebhookView(generics.GenericAPIView):
    """
    Click Shop API Webhook Endpoint (VC-101).
    Handles Prepare (action=0) and Complete (action=1) verified via MD5 signature.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from rest_framework.response import Response

        from .gateways import ClickGateway

        gateway = ClickGateway()
        payload = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        response_payload = gateway.process_webhook(payload, request.headers)
        return Response(response_payload)
