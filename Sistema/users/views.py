from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CustomUser
from .serializers import UserMeSerializer, UserSerializer, UserCreateSerializer, ResetPasswordSerializer
from .permissions import IsAdminOrDesarrollador


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user


class UserListCreate(generics.ListCreateAPIView):
    """Solo Admin y Desarrollador. Lista usuarios (incl. inactivos) y crea nuevos."""
    permission_classes = [IsAuthenticated, IsAdminOrDesarrollador]
    queryset = CustomUser.objects.all().order_by("-date_joined")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """Solo Admin y Desarrollador. Actualizar = soft delete si is_active=False."""
    permission_classes = [IsAuthenticated, IsAdminOrDesarrollador]
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class ResetPasswordView(APIView):
    """Solo Admin y Desarrollador. Resetea contraseña de un usuario."""
    permission_classes = [IsAuthenticated, IsAdminOrDesarrollador]

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        ser = ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user.set_password(ser.validated_data["new_password"])
        user.save()
        return Response({"detail": "Contraseña actualizada."})
