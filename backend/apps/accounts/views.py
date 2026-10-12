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
