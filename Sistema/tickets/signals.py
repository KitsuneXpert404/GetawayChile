from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket, TicketStatus
from notifications.signals import notify_roles
from notifications.models import Notification


@receiver(post_save, sender=Ticket)
def notify_ticket_changes(sender, instance, created, **kwargs):
    if created:
        # Notify the target role that a new ticket arrived
        actor = instance.creator
        message = (
            f"Nueva solicitud #{instance.id} de {actor.first_name} {actor.last_name}: "
            f"[{instance.get_ticket_type_display()}] {instance.title}"
        )
        link = f"/tickets/{instance.id}/"
        notify_roles([instance.target_role], message, actor=actor, link=link)
    else:
        # If ticket was responded, notify the creator
        if instance.status in [TicketStatus.APPROVED, TicketStatus.REJECTED, TicketStatus.CLOSED]:
            if instance.responded_by and instance.responded_by != instance.creator:
                responder_name = f"{instance.responded_by.first_name} {instance.responded_by.last_name}".strip()
                message = (
                    f"Tu solicitud #{instance.id} '{instance.title}' fue "
                    f"{instance.get_status_display()} por {responder_name}."
                )
                link = f"/tickets/{instance.id}/"
                Notification.objects.create(
                    recipient=instance.creator,
                    actor=instance.responded_by,
                    message=message,
                    link=link,
                )
