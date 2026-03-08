from datetime import datetime


def get_role_template(user):
    """
    Única fuente de verdad para determinar el template base según el rol del usuario.
    Usar esta función en TODAS las vistas — nunca escribir la lógica inline.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return 'core/base_dashboard.html'
    role = getattr(user, 'role', '')
    if role in ('ADMIN', 'DESARROLLADOR') or getattr(user, 'is_admin', False):
        return 'core/base_dashboard.html'
    if role == 'VENDEDOR':
        return 'core/base_vendedor.html'
    if role == 'LOGISTICA':
        return 'core/base_logistica.html'
    if role == 'CONDUCTOR':
        return 'core/base_conductor.html'
    return 'core/base_dashboard.html'  # fallback seguro


def notifications_processor(request):
    """Inject notification data and user display helpers into all templates."""
    if not request.user.is_authenticated:
        return {}

    from notifications.models import Notification
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)

    user = request.user
    first = (user.first_name or '').strip()
    last = (user.last_name or '').strip()
    initials = (first[:1] + last[:1]).upper() if (first or last) else user.username[:2].upper()
    display_name = first if first else user.username

    return {
        'unread_notifications_count': unread_qs.count(),
        'recent_notifications': unread_qs.select_related('actor')[:5],
        'user_initials': initials,
        'user_display_name': display_name,
        'user_role_label': getattr(user, 'get_role_display', lambda: '')(),
        'role_base_template': get_role_template(user),
    }
