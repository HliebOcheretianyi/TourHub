import logging

from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, TourHubTokenSerializer, MeSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(post=extend_schema(summary="Реєстрація", tags=["Автентифікація"]))
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # реєстрація не потребує токена

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info("User registered: id=%s", user.id)


@extend_schema_view(post=extend_schema(summary="Логін: видає access і refresh", tags=["Автентифікація"]))
class LoginView(TokenObtainPairView):
    serializer_class = TourHubTokenSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            # пароль і токени в лог не пишемо ніколи
            logger.warning("Failed login attempt for username=%r", username)
            raise
        logger.info("User logged in: username=%r", username)
        return response


@extend_schema_view(get=extend_schema(summary="Поточний користувач", tags=["Автентифікація"]))
class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user