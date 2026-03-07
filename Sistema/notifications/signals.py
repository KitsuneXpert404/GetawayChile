from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from sales.models import Sale, SaleStatus, PaymentStatus
from users.models import CustomUser
from .models import Notification


def notify_roles(roles, message, actor=None, link=''):
    """Create a Notification for all active users matching the given roles."""
    recipients = CustomUser.objects.filter(role__in=roles, is_active=True)
    notifications = [
        Notification(recipient=user, actor=actor, message=message, link=link)
        for user in recipients
        if user != actor  # don't notify yourself
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


@receiver(pre_save, sender=Sale)
def track_sale_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Sale.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_payment_status = old_instance.payment_status
        except Sale.DoesNotExist:
            pass


@receiver(post_save, sender=Sale)
def notify_new_sale(sender, instance, created, **kwargs):
    seller_name = (
        f"{instance.seller.first_name} {instance.seller.last_name}".strip()
        if instance.seller else "Sistema Web"
    )
    tour_name = instance.tour.name if getattr(instance, 'tour', None) else "Tour Privado / Multi-destino"
    
    date_str = '-'
    if instance.tour_date:
        if isinstance(instance.tour_date, str):
            parts = instance.tour_date.split('-')
            if len(parts) == 3:
                date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
            else:
                date_str = instance.tour_date
        else:
            date_str = instance.tour_date.strftime('%d/%m/%Y')

    link = f"/dashboard/sales/{instance.id}/"

    if created:
        message = (
            f"Nueva venta #{instance.id} registrada por {seller_name} — "
            f"{tour_name} para el {date_str}."
        )
        notify_roles(['ADMIN', 'LOGISTICA'], message, actor=instance.seller, link=link)
    else:
        # Check for status changes to notify the seller
        if getattr(instance, '_old_status', None) and instance.status != instance._old_status:
            if instance.status == SaleStatus.CANCELADA:
                msg = f"Tu Venta #{instance.id} ({tour_name}) ha sido CANCELADA por Administración."
                Notification.objects.create(recipient=instance.seller, message=msg, link=link)

        if getattr(instance, '_old_payment_status', None) and instance.payment_status != instance._old_payment_status:
            if instance.payment_status == PaymentStatus.PAID:
                msg = f"El pago de tu Venta #{instance.id} ({tour_name}) ha sido confirmado y está PAGADO."
                Notification.objects.create(recipient=instance.seller, message=msg, link=link)

