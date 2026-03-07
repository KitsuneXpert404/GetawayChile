from django.db import models
from simple_history.models import HistoricalRecords
from catalog.models import Tour
from users.models import CustomUser
from logistics.models import Vehicle

class PaymentStatus(models.TextChoices):
    PENDING = "PENDIENTE", "Pendiente"
    PARTIAL = "ABONADO", "Abonado"
    PAID = "PAGADO", "Pagado"

class Currency(models.TextChoices):
    CLP = "CLP", "Pesos Chilenos"
    USD = "USD", "Dólares"
    BRL = "BRL", "Reales Brasileños"

class LanguageChoices(models.TextChoices):
    ES = "ES", "Español"
    EN = "EN", "Inglés"
    PT = "PT", "Portugués"

class NationalityChoices(models.TextChoices):
    CL = "Chilena", "Chilena"
    BR = "Brasileña", "Brasileña"
    US = "Estadounidense", "Estadounidense"
    AR = "Argentina", "Argentina"
    PE = "Peruana", "Peruana"
    BO = "Boliviana", "Boliviana"
    CO = "Colombiana", "Colombiana"
    UY = "Uruguaya", "Uruguaya"
    PY = "Paraguaya", "Paraguaya"
    OTRA = "Otra", "Otra"

class SaleStatus(models.TextChoices):
    CONFIRMED = "CONFIRMADA", "Confirmada"
    PENDING_APPROVAL = "PENDIENTE", "Pendiente de Aprobación"
    CANCELLED = "CANCELADA", "Cancelada"

class SaleOrigin(models.TextChoices):
    DIRECT = "DIRECTO", "Directo"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    INSTAGRAM = "INSTAGRAM", "Instagram"
    AGENCY = "AGENCIA", "Agencia Externa"
    OTHER = "OTRO", "Otro"

class Sale(models.Model):
    # Basic Client Info (Embedded for MVP speed as per user request to not overcomplicate yet)
    client_first_name = models.CharField(max_length=100, verbose_name="Nombres Cliente", default="")
    client_last_name = models.CharField(max_length=100, verbose_name="Apellidos Cliente", default="")
    client_rut_passport = models.CharField(max_length=50, verbose_name="RUT/Pasaporte", default="00000000")
    client_nationality = models.CharField(max_length=50, choices=NationalityChoices.choices, default=NationalityChoices.CL, verbose_name="Nacionalidad")
    client_email = models.EmailField(verbose_name="Email", blank=True, default="")
    client_phone = models.CharField(max_length=50, verbose_name="Teléfono", default="")
    hotel_address = models.CharField(max_length=255, verbose_name="Hotel/Dirección de Recogida", blank=True, default="")

    # Tour Info
    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name="sales", null=True, blank=True)
    is_private = models.BooleanField(default=False, verbose_name="¿Es Venta Privada?")
    tour_date = models.DateField(verbose_name="Fecha del Tour", null=True, blank=True)
    tour_language = models.CharField(max_length=2, choices=LanguageChoices.choices, default=LanguageChoices.ES, verbose_name="Idioma del Tour")
    passengers_count = models.PositiveIntegerField(default=1, verbose_name="Cantidad Pasajeros")

    # Payment Info
    origin_channel = models.CharField(max_length=50, choices=SaleOrigin.choices, default=SaleOrigin.DIRECT, verbose_name="Origen de la Reserva")
    agency = models.ForeignKey('clients.Agency', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Agencia", related_name="sales")
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Total a Pagar", default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Monto Pagado")
    currency = models.CharField(max_length=10, choices=Currency.choices, default=Currency.CLP, verbose_name="Moneda")
    payment_status = models.CharField(
        max_length=20, 
        choices=PaymentStatus.choices, 
        default=PaymentStatus.PENDING,
        verbose_name="Estado Pago"
    )
    status = models.CharField(
        max_length=20, 
        choices=SaleStatus.choices, 
        default=SaleStatus.CONFIRMED,
        verbose_name="Estado de Venta"
    )
    voucher_image = models.ImageField(upload_to='vouchers/%Y/%m/', blank=True, null=True, verbose_name="Comprobante 1")
    voucher_image_2 = models.ImageField(upload_to='vouchers/%Y/%m/', blank=True, null=True, verbose_name="Comprobante 2")
    voucher_image_3 = models.ImageField(upload_to='vouchers/%Y/%m/', blank=True, null=True, verbose_name="Comprobante 3")

    # Private Tour Info
    private_trip_description = models.TextField(blank=True, verbose_name="Descripción del viaje (Privado)")
    private_trip_observations = models.TextField(blank=True, verbose_name="Observaciones (Privado)")

    # Logistics / Dispatch Info
    assigned_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_sales", verbose_name="Vehículo / Agencia Asignada")
    pickup_time = models.TimeField(null=True, blank=True, verbose_name="Hora de Recogida")
    logistics_notes = models.TextField(blank=True, verbose_name="Notas de Logística (Internas)")

    # Confirmation traceability
    confirmed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="confirmations_made", verbose_name="Confirmado por"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Confirmado el")
    cancellation_reason = models.TextField(blank=True, verbose_name="Motivo de Cancelación")

    # Client notification
    client_notified = models.BooleanField(default=False, verbose_name="Cliente Notificado")
    client_notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Notificado el")

    # Meta
    seller = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="sales_made", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        db_table = "sales_sale"
        verbose_name = "Venta / Reserva"
        verbose_name_plural = "Ventas / Reservas"
        ordering = ['-created_at']

    @property
    def client_name(self):
        return f"{self.client_first_name} {self.client_last_name}".strip() or "Sin nombre"

    @property
    def is_multidestination(self):
        return self.tour_stops.count() > 1

    def recalculate_total(self):
        """Sum all SaleTour subtotals and save."""
        total = sum(s.subtotal for s in self.tour_stops.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return f"#{self.pk} - {self.client_name}"


class SaleTour(models.Model):
    """One row per tour destination within a sale (supports multi-destination trips)."""

    class StopStatus(models.TextChoices):
        PENDING   = 'PENDIENTE',  'Pendiente'
        CONFIRMED = 'CONFIRMADA', 'Confirmada'
        CANCELLED = 'CANCELADA',  'Cancelada'

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='tour_stops')
    tour = models.ForeignKey(
        'catalog.Tour', on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='Tour'
    )
    tour_date = models.DateField(null=True, blank=True, verbose_name='Fecha')
    tour_language = models.CharField(
        max_length=2, choices=LanguageChoices.choices, default=LanguageChoices.ES,
        verbose_name='Idioma'
    )
    is_private = models.BooleanField(default=False, verbose_name='Privado')
    private_description = models.TextField(blank=True, verbose_name='Descripción privada')

    # Pax & Pricing
    pax_adults = models.PositiveIntegerField(default=1, verbose_name='Adultos')
    pax_infants = models.PositiveIntegerField(default=0, verbose_name='Infantes')
    price_adult = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='Precio Adulto')
    price_infant = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='Precio Infante')
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='Subtotal')

    order = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')

    # Per-stop confirmation
    stop_status = models.CharField(
        max_length=12,
        choices=StopStatus.choices,
        default=StopStatus.PENDING,
        verbose_name='Estado del Stop',
    )
    stop_confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmado en')
    stop_confirmed_by = models.ForeignKey(
        'users.CustomUser', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name='Confirmado por'
    )
    stop_cancellation_reason = models.TextField(blank=True, verbose_name='Motivo de cancelación')

    # Per-stop logistics assignment
    assigned_vehicle = models.ForeignKey(
        'logistics.Vehicle', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stop_assignments', verbose_name='Vehículo Asignado'
    )
    pickup_time = models.TimeField(null=True, blank=True, verbose_name='Hora de Recogida')
    logistics_notes = models.TextField(blank=True, verbose_name='Notas de Logística (Internas)')
    vehicle_assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Vehículo asignado en')
    vehicle_assigned_by = models.ForeignKey(
        'users.CustomUser', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='stop_vehicle_assignments', verbose_name='Asignado por'
    )

    class Meta:
        db_table = 'sales_sale_tour'
        ordering = ['order', 'id']
        verbose_name = 'Destino de Venta'
        verbose_name_plural = 'Destinos de Venta'

    def __str__(self):
        tour_name = self.tour.name if self.tour else 'Tour Privado'
        return f"Venta #{self.sale_id} – {tour_name} ({self.tour_date})"

    @property
    def is_stop_confirmed(self):
        return self.stop_status == self.StopStatus.CONFIRMED

    @property
    def is_stop_cancelled(self):
        return self.stop_status == self.StopStatus.CANCELLED


class Passenger(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="passengers")
    first_name = models.CharField(max_length=100, verbose_name="Nombres", default="")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos", default="")
    rut_passport = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50, choices=NationalityChoices.choices, default=NationalityChoices.CL, verbose_name="Nacionalidad")

    class Meta:
        db_table = "sales_passenger"

