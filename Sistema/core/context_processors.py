from datetime import datetime


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

    # Dynamic template inheritance based on role
    role_base_template = 'core/base_dashboard.html' # Default (Admin view)
    if user.is_admin:
        role_base_template = 'core/base_dashboard.html'
    elif getattr(user, 'role', '') == 'VENDEDOR':
        role_base_template = 'core/base_vendedor.html'
    elif getattr(user, 'role', '') == 'LOGISTICA':
        role_base_template = 'core/base_logistica.html'
    elif getattr(user, 'role', '') == 'CONDUCTOR':
        role_base_template = 'core/base_conductor.html'

    return {
        'unread_notifications_count': unread_qs.count(),
        'recent_notifications': unread_qs.select_related('actor')[:5],
        'user_initials': initials,
        'user_display_name': display_name,
        'user_role_label': getattr(user, 'get_role_display', lambda: '')(),
        'role_base_template': role_base_template,
    }
