from rest_framework import permissions


class IsAdminOrDesarrollador(permissions.BasePermission):
    """Solo Admin (Dueño) y Desarrollador. Para Gestión de Usuarios y acciones de superusuario."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ("ADMIN", "DESARROLLADOR")


class IsAdminOrLogistica(permissions.BasePermission):
    """Admin o Logística. Para aprobar sobrecupos, asignar conductores, confirmar viajes."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ("ADMIN", "LOGISTICA")


class IsAdminOrLogisticaOrReadOnly(permissions.BasePermission):
    """Lectura (GET) para cualquier usuario autenticado; creación/edición/borrado solo ADMIN o LOGISTICA."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in ("ADMIN", "LOGISTICA")
