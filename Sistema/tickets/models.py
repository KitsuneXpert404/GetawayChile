from django.db import models
from users.models import CustomUser
from catalog.models import Tour


class TicketType(models.TextChoices):
    SOBRECUPO = 'SOBRECUPO', 'Solicitud de Sobrecupo'
    CAMBIO = 'CAMBIO', 'Solicitud de Cambio de Tour'
    CONSULTA = 'CONSULTA', 'Consulta General'
    INCIDENCIA = 'INCIDENCIA', 'Incidencia / Problema'
    OTRO = 'OTRO', 'Otro'


class TicketStatus(models.TextChoices):
    PENDING = 'PENDIENTE', 'Pendiente'
    IN_REVIEW = 'EN_REVISION', 'En Revisión'
    APPROVED = 'APROBADA', 'Aprobada'
    REJECTED = 'RECHAZADA', 'Rechazada'
    CLOSED = 'CERRADA', 'Cerrada'


class TargetRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administración'
    LOGISTICA = 'LOGISTICA', 'Logística'


class Ticket(models.Model):
    creator = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='created_tickets', verbose_name='Creador'
    )
    target_role = models.CharField(
        max_length=20, choices=TargetRole.choices, default=TargetRole.LOGISTICA,
        verbose_name='Dirigido a'
    )
    ticket_type = models.CharField(
        max_length=20, choices=TicketType.choices, default=TicketType.CONSULTA,
        verbose_name='Tipo de Solicitud'
    )
    title = models.CharField(max_length=200, verbose_name='Asunto')
    description = models.TextField(verbose_name='Descripción')
    status = models.CharField(
        max_length=20, choices=TicketStatus.choices, default=TicketStatus.PENDING,
        verbose_name='Estado'
    )

    # Optional references
    tour = models.ForeignKey(
        Tour, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets', verbose_name='Tour Relacionado'
    )
    tour_date = models.DateField(null=True, blank=True, verbose_name='Fecha del Tour')

    # Response
    responded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='responded_tickets', verbose_name='Respondido por'
    )
    response = models.TextField(blank=True, default='', verbose_name='Respuesta')
    responded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets / Solicitudes'

    def __str__(self):
        return f"#{self.id} [{self.get_ticket_type_display()}] {self.title} — {self.get_status_display()}"

    @property
    def is_open(self):
        return self.status in [TicketStatus.PENDING, TicketStatus.IN_REVIEW]

    @property
    def status_color(self):
        colors = {
            TicketStatus.PENDING: 'warning',
            TicketStatus.IN_REVIEW: 'info',
            TicketStatus.APPROVED: 'success',
            TicketStatus.REJECTED: 'danger',
            TicketStatus.CLOSED: 'secondary',
        }
        return colors.get(self.status, 'secondary')
