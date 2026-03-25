"""
notifications/whatsapp.py
Sends WhatsApp messages via Twilio.
Language auto-detected from client's nationality.
"""
import logging
import re
import os

logger = logging.getLogger(__name__)

# ── Nationality → Language map ─────────────────────────────────────
_NATIONALITY_LANG = {
    'Brasileña': 'PT',
    'Estadounidense': 'EN',
}
_ENGLISH_SPEAKING = {'Estadounidense', 'Otra'}


def get_language_for_nationality(nationality: str) -> str:
    """Return 'PT', 'EN', or 'ES' based on the client's nationality."""
    if nationality == 'Brasileña':
        return 'PT'
    if nationality in _ENGLISH_SPEAKING:
        return 'EN'
    return 'ES'


# ── Message templates ──────────────────────────────────────────────
def _build_message(sale, lang: str, stops=None, custom_message: str = None) -> str:
    """Build WhatsApp message. `stops` is an iterable of SaleTour objects.
    If None, all stops of the sale are used."""
    name = f"{sale.client_first_name} {sale.client_last_name}".strip()
    booking = sale.pk
    hotel = sale.hotel_address or ('Sin especificar' if lang == 'ES' else ('Not specified' if lang == 'EN' else 'Não especificado'))
    pax = sale.passengers_count

    # Build tour summary — include per-stop pickup time
    if stops is None:
        stops = list(sale.tour_stops.select_related('tour').all())
    else:
        stops = list(stops)

    if stops:
        tour_lines = []
        for s in stops:
            tour_name = s.tour.name if s.tour else ('Tour Privado' if lang == 'ES' else ('Private Tour' if lang == 'EN' else 'Tour Privado'))
            date_str = s.tour_date.strftime('%d/%m/%Y') if s.tour_date else '---'
            # Use stop-level pickup time, fall back to sale-level
            stop_pickup = s.pickup_time or sale.pickup_time
            if stop_pickup:
                tour_lines.append(f"  • {tour_name} — {date_str} | ⏰ {stop_pickup.strftime('%H:%M')}")
            else:
                tour_lines.append(f"  • {tour_name} — {date_str}")
        tour_text = '\n'.join(tour_lines)
    else:
        tour_text = '  • A confirmar'


    # Build passenger list
    passengers = list(sale.passengers.all())
    if passengers:
        if lang == 'PT':
            pax_header = "👥 *Passageiros:*"
        elif lang == 'EN':
            pax_header = "👥 *Passengers:*"
        else:
            pax_header = "👥 *Pasajeros:*"
        pax_lines = [pax_header]
        for i, p in enumerate(passengers, 1):
            doc = f" | {p.rut_passport}" if p.rut_passport else ""
            pax_lines.append(f"  {i}. {p.first_name} {p.last_name}{doc}")
        pax_text = '\n'.join(pax_lines) + '\n'
    else:
        if lang == 'PT':
            pax_text = f"👥 *Passageiros:* {pax}\n"
        elif lang == 'EN':
            pax_text = f"👥 *Passengers:* {pax}\n"
        else:
            pax_text = f"👥 *Pasajeros:* {pax}\n"

    # Format Financials
    sym = 'US$' if sale.currency == 'USD' else ('R$' if sale.currency == 'BRL' else '$')
    balance = sale.total_amount - sale.amount_paid
    if lang == 'PT':
        fin_text = f"💰 *Pagamento:*\n  • Total: {sym}{sale.total_amount:,.0f}\n  • Pago: {sym}{sale.amount_paid:,.0f}\n" + (f"  • *Saldo devedor:* {sym}{balance:,.0f}\n" if balance > 0 else "")
    elif lang == 'EN':
        fin_text = f"💰 *Payment:*\n  • Total: {sym}{sale.total_amount:,.0f}\n  • Paid: {sym}{sale.amount_paid:,.0f}\n" + (f"  • *Balance due:* {sym}{balance:,.0f}\n" if balance > 0 else "")
    else:
        fin_text = f"💰 *Pagos:*\n  • Total: {sym}{sale.total_amount:,.0f}\n  • Pagado: {sym}{sale.amount_paid:,.0f}\n" + (f"  • *Saldo pendiente:* {sym}{balance:,.0f}\n" if balance > 0 else "")

    obs_text = ""
    if custom_message:
        obs_title = "📌 *Observações:*" if lang == 'PT' else ("📌 *Notes:*" if lang == 'EN' else "📌 *Observaciones:*")
        obs_text = f"\n{obs_title}\n{custom_message}\n"

    if lang == 'PT':
        return (
            f"✈️ *Reserva Confirmada!* — Getaway Chile\n\n"
            f"Olá *{name}*, sua reserva *#{booking}* foi CONFIRMADA com sucesso! 🎉\n\n"
            f"📋 *Detalhes da sua reserva:*\n"
            f"{tour_text}\n"
            f"📍 *Endereço de coleta:* {hotel}\n"
            f"{pax_text}\n"
            f"{fin_text}"
            f"{obs_text}\n"
            f"Por favor, esteja no local *10 minutos antes* do horário indicado.\n"
            f"Leve documento de identidade ou passaporte válido.\n\n"
            f"Até logo! 🌄\n"
            f"*Getaway Chile* — Turismo de Aventura"
        )
    elif lang == 'EN':
        return (
            f"✈️ *Booking Confirmed!* — Getaway Chile\n\n"
            f"Hello *{name}*, your booking *#{booking}* is CONFIRMED! 🎉\n\n"
            f"📋 *Booking details:*\n"
            f"{tour_text}\n"
            f"📍 *Pick-up address:* {hotel}\n"
            f"{pax_text}\n"
            f"{fin_text}"
            f"{obs_text}\n"
            f"Please be ready at the pick-up location *10 minutes early*.\n"
            f"Bring a valid ID or passport.\n\n"
            f"See you soon! 🌄\n"
            f"*Getaway Chile* — Adventure & Experiences"
        )
    else:  # ES
        return (
            f"✈️ *¡Reserva Confirmada!* — Getaway Chile\n\n"
            f"Hola *{name}*, tu reserva *#{booking}* está CONFIRMADA. 🎉\n\n"
            f"📋 *Detalles de tu reserva:*\n"
            f"{tour_text}\n"
            f"📍 *Dirección de recogida:* {hotel}\n"
            f"{pax_text}\n"
            f"{fin_text}"
            f"{obs_text}\n"
            f"Por favor, espera en el lugar indicado *10 minutos antes* de la hora.\n"
            f"Lleva documento de identidad o pasaporte vigente.\n\n"
            f"¡Nos vemos pronto! 🌄\n"
            f"*Getaway Chile* — Turismo de Aventura y Experiencias"
        )


# ── Phone normalization ────────────────────────────────────────────
def _normalize_phone(phone: str, nationality: str) -> str | None:
    """
    Return E.164 format (+XXXXXXXXXXX) or None if unparseable.
    If no country code, infer from nationality.
    """
    if not phone:
        return None
    # Strip everything except digits and leading +
    digits_only = re.sub(r'[^\d+]', '', phone.strip())
    if digits_only.startswith('+'):
        return digits_only  # already has country code
    # Infer country code from nationality
    _country_codes = {
        'Chilena': '56',
        'Argentina': '54',
        'Peruana': '51',
        'Boliviana': '591',
        'Colombiana': '57',
        'Uruguaya': '598',
        'Paraguaya': '595',
        'Brasileña': '55',
        'Estadounidense': '1',
    }
    code = _country_codes.get(nationality, '56')  # default Chile
    # Remove leading zeros if any
    digits_only = digits_only.lstrip('0')
    return f"+{code}{digits_only}"


# ── Main send functions ──────────────────────────────────────────────
def _ultramsg_send(sale, to_phone: str, body: str, lang: str) -> tuple[bool, str]:
    """Low-level Ultramsg send. Returns (success, message)."""
    import urllib.request
    import urllib.parse
    
    instance_id = os.environ.get('ULTRAMSG_INSTANCE_ID', '').strip()
    token = os.environ.get('ULTRAMSG_TOKEN', '').strip()
    
    if not instance_id or not token:
        return False, 'Ultramsg no configurado (ULTRAMSG_INSTANCE_ID / ULTRAMSG_TOKEN vacíos)'
        
    # Ultramsg needs the phone number without the leading '+'
    if to_phone.startswith('+'):
        to_phone = to_phone[1:]
        
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    data = urllib.parse.urlencode({
        'token': token,
        'to': to_phone,
        'body': body
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data)
        req.add_header('content-type', 'application/x-www-form-urlencoded')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Agregamos timeout de 10 segundos para evitar que Render se quede colgado (502)
        response = urllib.request.urlopen(req, timeout=10)
        if response.getcode() == 200:
            lang_name = 'Español' if lang == 'ES' else ('Inglés' if lang == 'EN' else 'Portugués')
            sale_info = f" (Sale #{sale.pk})" if sale and hasattr(sale, 'pk') else ""
            logger.info(f'WhatsApp (Ultramsg) sent to {to_phone}{sale_info} — lang={lang}')
            return True, f'WhatsApp enviado a {to_phone} en {lang_name}'
        else:
            return False, f'Error HTTP de Ultramsg: {response.getcode()}'
            
    except Exception as exc:
        sale_info = f" sale #{sale.pk}" if sale and hasattr(sale, 'pk') else ""
        logger.error(f'WhatsApp (Ultramsg) send failed for{sale_info}: {exc}')
        return False, str(exc)


def send_whatsapp_notification(sale) -> tuple[bool, str]:
    """Legacy helper: send WA for all stops of a sale."""
    if not sale.client_phone:
        return False, 'El cliente no tiene número de teléfono registrado'
    to_phone = _normalize_phone(sale.client_phone, sale.client_nationality)
    if not to_phone:
        return False, f'Número de teléfono inválido: {sale.client_phone}'
    lang = get_language_for_nationality(sale.client_nationality)
    body = _build_message(sale, lang)
    return _ultramsg_send(sale, to_phone, body, lang)


def send_whatsapp_notification_for_stops(sale, stops, lang: str, custom_msg: str = "") -> tuple[bool, str]:
    """
    Send WhatsApp notification for a specific list of SaleTour stops.
    Used when the user selects a particular tour stop to notify about.
    """
    if not sale.client_phone:
        return False, 'El cliente no tiene número de teléfono registrado'
    to_phone = _normalize_phone(sale.client_phone, sale.client_nationality)
    if not to_phone:
        return False, f'Número de teléfono inválido: {sale.client_phone}'
    body = _build_message(sale, lang, stops=stops)
    if custom_msg:
        body += f"\n\nObservaciones:\n{custom_msg}"
    return _ultramsg_send(sale, to_phone, body, lang)
