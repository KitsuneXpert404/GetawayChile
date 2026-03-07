from django.db import models
from users.models import CustomUser


class Notification(models.Model):
    recipient = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='notifications', verbose_name='Destinatario'
    )
    actor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_notifications', verbose_name='Actor'
    )
    message = models.TextField(verbose_name='Mensaje')
    link = models.CharField(max_length=500, blank=True, default='', verbose_name='Enlace')
    is_read = models.BooleanField(default=False, verbose_name='Leída')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"→ {self.recipient.username}: {self.message[:50]}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
