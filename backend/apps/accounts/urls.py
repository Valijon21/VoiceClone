from django.urls import path

from .views import (
    AdminUserListView,
    AdminUserPlanUpdateView,
    LoginView,
    LogoutView,
    MeView,
    QuotaStatusView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("quota/", QuotaStatusView.as_view(), name="quota"),
    path("users/", AdminUserListView.as_view(), name="admin_users_list"),
    path("users/<uuid:pk>/plan/", AdminUserPlanUpdateView.as_view(), name="admin_user_plan_update"),
]
