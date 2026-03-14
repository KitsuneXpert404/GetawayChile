from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin (Dueño)"
    VENDEDOR = "VENDEDOR", "Vendedor"
    LOGISTICA = "LOGISTICA", "Logística"
    CONDUCTOR = "CONDUCTOR", "Conductor"
    GUIA = "GUIA", "Guía"
    DESARROLLADOR = "DESARROLLADOR", "Desarrollador"


class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.VENDEDOR
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    rut = models.CharField(max_length=12, blank=True, null=True, unique=True, verbose_name="RUT")
    second_name = models.CharField(max_length=150, blank=True, verbose_name="Segundo Nombre")
    second_last_name = models.CharField(max_length=150, blank=True, verbose_name="Apellido Materno")
    personal_email = models.EmailField(blank=True, null=True, verbose_name="Correo Personal")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name="Foto de Perfil")
    requires_password_change = models.BooleanField(default=True, verbose_name="Requiere Cambio de Contraseña")

    class Meta:
        db_table = "users_user"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_online(self):
        from django.core.cache import cache
        return cache.get(f'seen_user_{self.id}') is not None
        
    @property
    def get_last_activity(self):
        from django.core.cache import cache
        last_seen = cache.get(f'seen_user_{self.id}')
        if last_seen:
            return last_seen
        return self.last_login

    @property
    def is_logistica(self):
        return self.role == Role.LOGISTICA or self.is_admin

    @property
    def is_vendedor(self):
        return self.role == Role.VENDEDOR or self.is_admin

    @property
    def is_guia(self):
        return self.role == Role.GUIA or self.is_admin
