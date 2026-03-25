"""
Public-facing views for the Getaway Chile client website.
These views are completely separate from the ERP/dashboard system.
No login required. All content is public.
"""
import datetime
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings

from catalog.models import Tour, TourType
from notifications.models import Notification
from users.models import CustomUser


def _get_sellers_and_admins():
    """Return all active users who are sellers or admins (who receive reservations)."""
    return CustomUser.objects.filter(
        is_active=True,
        role__in=['VENDEDOR', 'ADMIN']
    )


class PublicHomeView(TemplateView):
    """Landing home page for public clients."""
    template_name = 'core/public/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['featured_tours'] = Tour.objects.filter(active=True).order_by('?')[:3]
        ctx['total_tours'] = Tour.objects.filter(active=True).count()
        return ctx


class PublicToursView(TemplateView):
    """Public catalog of regular tours."""
    template_name = 'core/public/tours.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tours'] = Tour.objects.filter(active=True, tour_type=TourType.REGULAR).order_by('name')
        # Distinct destinations for filter bar
        destinations = (
            Tour.objects.filter(active=True, tour_type=TourType.REGULAR)
            .exclude(destination='')
            .values_list('destination', flat=True)
            .distinct()
            .order_by('destination')
        )
        ctx['destinations'] = list(destinations)
        return ctx


class PublicTourDetailView(TemplateView):
    """Detail view for a specific tour."""
    template_name = 'core/public/tour_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tour = Tour.objects.get(pk=self.kwargs['pk'])
        ctx['tour'] = tour
        # For the placeholder Unsplash images matching the catalog
        ctx['ph_index'] = (tour.pk % 6) + 1
        return ctx


class PublicToursPrivadosView(TemplateView):
    """Public catalog of private tours."""
    template_name = 'core/public/tours_privados.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tours'] = Tour.objects.filter(active=True, tour_type=TourType.PRIVADO).order_by('name')
        ctx['benefits'] = [
            {'icon': 'calendar-alt',   'title': 'Tu horario, tus reglas',         'desc': 'Salida a la hora que elijas, sin esperas ni grupos grandes.'},
            {'icon': 'users',          'title': 'Solo tu grupo',                   'desc': 'El guía y el vehículo son exclusivamente para ti y tus acompañantes.'},
            {'icon': 'route',          'title': 'Itinerario personalizado',        'desc': 'Diseñamos la ruta según tus intereses, ritmo y preferencias.'},
            {'icon': 'language',       'title': 'Guías bilingües',                 'desc': 'Español, English y Português para viajeros internacionales.'},
            {'icon': 'camera',         'title': 'Tiempo para cada momento',        'desc': 'Sin prisas. El tour se adapta a ti, no al revés.'},
            {'icon': 'concierge-bell', 'title': 'Servicio premium incluido',       'desc': 'Vehículo de lujo, agua a bordo y asistencia permanente.'},
        ]
        return ctx


class PublicTransporteView(TemplateView):
    """Airport transport / executive transfer page."""
    template_name = 'core/public/transporte.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['features'] = [
            {'icon': 'plane-arrival',  'title': 'Seguimiento de vuelo',       'desc': 'Monitoreamos tu vuelo en tiempo real y ajustamos si hay retrasos.'},
            {'icon': 'user-tie',       'title': 'Conductores profesionales',   'desc': 'Chóferes con experiencia, uniforme y conocimiento de la región.'},
            {'icon': 'shuttle-van',    'title': 'Vehículos cómodos',           'desc': 'Furgones modernos con aire acondicionado y espacio para equipaje.'},
            {'icon': 'clock',          'title': 'Puntualidad garantizada',     'desc': 'Estamos en el aeropuerto antes que tú, sin excepciones.'},
        ]
        ctx['steps'] = [
            {'title': 'Haz tu reserva',           'desc': 'Completa el formulario con tu vuelo, fecha y número de pasajeros. Te confirmamos en menos de 24 horas.'},
            {'title': 'Recibe la confirmación',   'desc': 'Te enviamos los datos del conductor y el vehículo asignado por WhatsApp o email.'},
            {'title': 'Día del traslado',          'desc': 'El conductor te espera con un cartel con tu nombre en la salida del terminal. Solo súbete y disfruta.'},
            {'title': 'Llegada a destino',         'desc': 'Te dejamos en la puerta de tu hotel, hostal o dirección que indiques. Seguro, rápido y cómodo.'},
        ]
        return ctx


class PublicQuienesSomosView(TemplateView):
    """About us page."""
    template_name = 'core/public/quienes_somos.html'


class PublicContactoView(View):
    """Contact form — GET shows form, POST sends email notification to team."""
    template_name = 'core/public/contacto.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        nombre   = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email    = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        mensaje  = request.POST.get('mensaje', '').strip()

        if not nombre or not email or not mensaje:
            return render(request, self.template_name, {'error': True})

        full_name = f"{nombre} {apellido}".strip()
        body = (
            f"📬 NUEVO MENSAJE DE CONTACTO (Web Pública)\n"
            f"{'='*50}\n"
            f"Nombre:    {full_name}\n"
            f"Email:     {email}\n"
            f"Teléfono:  {telefono or '—'}\n"
            f"{'='*50}\n"
            f"Mensaje:\n{mensaje}\n"
        )

        # Email to team
        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(
                subject=f"[Web] Consulta de {full_name}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass

        # In-app notification to all sellers + admins
        notif_msg = (
            f"📬 Nueva consulta web de {full_name} ({email})"
            f"{' — Tel: ' + telefono if telefono else ''}. "
            f"Mensaje: «{mensaje[:80]}{'...' if len(mensaje) > 80 else ''}»"
        )
        for user in _get_sellers_and_admins():
            Notification.objects.create(
                recipient=user,
                message=notif_msg,
                link='/dashboard/',
            )

        return render(request, self.template_name, {'success': True})


class PublicReservarView(View):
    """Reservation request form — sends notification to all sellers and admins."""
    template_name = 'core/public/reservar.html'

    def _get_context(self):
        return {
            'tours': Tour.objects.filter(active=True).order_by('name'),
            'today': datetime.date.today().isoformat(),
        }

    def get(self, request):
        return render(request, self.template_name, self._get_context())

    def post(self, request):
        nombre     = request.POST.get('nombre', '').strip()
        apellido   = request.POST.get('apellido', '').strip()
        email      = request.POST.get('email', '').strip()
        telefono   = request.POST.get('telefono', '').strip()
        pais       = request.POST.get('pais', '').strip()
        idioma     = request.POST.get('idioma', 'es')
        tour_id    = request.POST.get('tour_id', '').strip()
        fecha      = request.POST.get('fecha', '').strip()
        personas   = request.POST.get('personas', '').strip()
        tipo_grupo = request.POST.get('tipo_grupo', '').strip()
        mensaje    = request.POST.get('mensaje', '').strip()

        if not nombre or not email or not fecha or not personas:
            ctx = self._get_context()
            ctx['error'] = True
            return render(request, self.template_name, ctx)

        # Resolve tour name
        tour_name = 'No especificado'
        if tour_id == 'transporte':
            tour_name = '🚐 Transporte al Aeropuerto'
        elif tour_id == 'parque_acuatico':
            tour_name = '💦 Transporte Parque Acuático'
        elif tour_id == 'empresa':
            tour_name = '🏢 Transporte Corporativo'
        elif tour_id == 'playa':
            tour_name = '🏖️ Viaje Privado a la Playa'
        elif tour_id == 'matrimonio':
            tour_name = '💍 Transporte Matrimonio'
        elif tour_id == 'personalizado':
            tour_name = '✨ Tour Personalizado'
        elif tour_id:
            try:
                tour_obj = Tour.objects.get(pk=int(tour_id))
                tour_name = tour_obj.name
            except (Tour.DoesNotExist, ValueError):
                tour_name = 'Tour seleccionado'

        full_name = f"{nombre} {apellido}".strip()
        idioma_display = {'es': 'Español', 'en': 'English', 'pt': 'Português'}.get(idioma, idioma)
        tipo_display = {
            'familia': 'Familia', 'pareja': 'Pareja', 'amigos': 'Amigos',
            'corporativo': 'Corporativo', 'solo': 'Viajero Solo'
        }.get(tipo_grupo, tipo_grupo)

        body = (
            f"🗓️ NUEVA SOLICITUD DE RESERVA (Web Pública)\n"
            f"{'='*55}\n"
            f"CLIENTE\n"
            f"  Nombre:      {full_name}\n"
            f"  Email:       {email}\n"
            f"  Teléfono:    {telefono or '—'}\n"
            f"  País:        {pais or '—'}\n"
            f"  Idioma:      {idioma_display}\n"
            f"\nDETALLES DEL TOUR\n"
            f"  Tour:        {tour_name}\n"
            f"  Fecha:       {fecha}\n"
            f"  Personas:    {personas}\n"
            f"  Tipo grupo:  {tipo_display or '—'}\n"
            f"\nMENSAJE ADICIONAL\n"
            f"  {mensaje or '(Sin mensaje adicional)'}\n"
            f"{'='*55}\n"
            f"Responder a: {email}\n"
        )

        # Email to team
        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(
                subject=f"🗓️ [RESERVA WEB] {full_name} → {tour_name} ({fecha})",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass

        # In-app notification to all sellers + admins with full client contact
        notif_msg = (
            f"🗓️ Nueva solicitud de reserva — {full_name} "
            f"({'📧 ' + email}{' · 📞 ' + telefono if telefono else ''}) "
            f"para «{tour_name}» el {fecha}. "
            f"{personas} persona(s). Idioma: {idioma_display}."
        )
        for user in _get_sellers_and_admins():
            Notification.objects.create(
                recipient=user,
                message=notif_msg,
                link='/dashboard/',
            )

        ctx = self._get_context()
        ctx['success'] = True
        return render(request, self.template_name, ctx)
