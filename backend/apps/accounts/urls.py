from django.urls import path

from .views import (
    AdminRefundProcessView,
    AdminUserListView,
    AdminUserPlanUpdateView,
    CheckoutInitiateView,
    ClickWebhookView,
    LoginView,
    LogoutView,
    MeView,
    PaymentTransactionListView,
    PaymeWebhookView,
    QuotaStatusView,
    RegisterView,
    SimulatePaymentFailureView,
    SubscriptionCancelView,
    SubscriptionDetailView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("quota/", QuotaStatusView.as_view(), name="quota"),
    path("subscription/", SubscriptionDetailView.as_view(), name="subscription_detail"),
    path("subscription/cancel/", SubscriptionCancelView.as_view(), name="subscription_cancel"),
    path(
        "subscription/transactions/",
        PaymentTransactionListView.as_view(),
        name="subscription_transactions",
    ),
    path(
        "subscription/simulate-failure/",
        SimulatePaymentFailureView.as_view(),
        name="subscription_simulate_failure",
    ),
    path("subscription/refund/", AdminRefundProcessView.as_view(), name="admin_refund_process"),
    path("payments/checkout/", CheckoutInitiateView.as_view(), name="payment_checkout"),
    path("payments/payme/webhook/", PaymeWebhookView.as_view(), name="payme_webhook"),
    path("payments/click/webhook/", ClickWebhookView.as_view(), name="click_webhook"),
    path("users/", AdminUserListView.as_view(), name="admin_users_list"),
    path("users/<uuid:pk>/plan/", AdminUserPlanUpdateView.as_view(), name="admin_user_plan_update"),
]
