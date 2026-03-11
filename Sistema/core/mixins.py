"""
Mixins centralizados de permisos por rol — ERP Getaway Chile.
Usar en vistas (CBV) para restringir acceso por rol de forma consistente.
"""
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Solo ADMIN (dueño). Para acciones exclusivas del dueño."""
    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (getattr(u, "is_admin", False) or u.role == "ADMIN")


class AdminOrDesarrolladorRequiredMixin(UserPassesTestMixin):
    """ADMIN o DESARROLLADOR. Para gestión de usuarios (crear, editar, desactivar)."""
    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in ("ADMIN", "DESARROLLADOR")


class AdminOrLogisticsRequiredMixin(UserPassesTestMixin):
    """ADMIN o LOGISTICA. Para reportes, historial, catálogo, agencias, operaciones."""
    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (
            getattr(u, "is_admin", False) or getattr(u, "is_logistica", False) or u.role in ("ADMIN", "LOGISTICA")
        )


# Alias para uso en app logistics (mismo criterio que AdminOrLogisticsRequiredMixin)
LogisticsRequiredMixin = AdminOrLogisticsRequiredMixin
