from django.db import models
from catalog.models import Tour
from users.models import CustomUser

class OperationStatus(models.TextChoices):
    PENDING = "PENDIENTE", "Pendiente"
    CONFIRMED = "CONFIRMADO", "Confirmado"
    COMPLETED = "REALIZADO", "Realizado"
    CANCELLED = "CANCELADO", "Cancelado"

class VehicleType(models.TextChoices):
    MINIVAN     = 'MINIVAN',   'Minivan'
    BUS         = 'BUS',       'Bus'
    MICROBUS    = 'MICROBUS',  'Microbús'
    VAN         = 'VAN',       'Van / Furgón'
    SUV         = 'SUV',       'SUV / 4x4'
    SEDAN       = 'SEDAN',     'Sedan'
    OTHER       = 'OTHER',     'Otro'

class Vehicle(models.Model):
    # Vehicle identity
    plate         = models.CharField(max_length=20, unique=True, verbose_name="Patente / Placa")
    vehicle_type  = models.CharField(max_length=20, choices=VehicleType.choices,
                                     default=VehicleType.VAN, verbose_name="Tipo de Vehículo")
    vehicle_year  = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Año del Vehículo")
    vehicle_color = models.CharField(max_length=60, blank=True, verbose_name="Color")
    owner_company = models.CharField(max_length=150, verbose_name="Dueño / Agencia",
                                     help_text="Ej: Empresa XYZ o Juan Pérez")
    capacity      = models.PositiveIntegerField(verbose_name="Capacidad de Pasajeros", default=4)
    is_active     = models.BooleanField(default=True, verbose_name="Vehículo Activo")

    # Default driver (system user with CONDUCTOR role — optional)
    default_driver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="default_vehicles",
        verbose_name="Conductor por Defecto (usuario del sistema)",
        limit_choices_to={'role': 'CONDUCTOR'}
    )

    # External driver contact (for drivers NOT in the system)
    driver_name   = models.CharField(max_length=120, blank=True, verbose_name="Nombre del Conductor")
    driver_phone  = models.CharField(max_length=30, blank=True,
                                     verbose_name="Teléfono / WhatsApp del Conductor",
                                     help_text="Formato internacional. Ej: +56912345678")
    driver_email  = models.CharField(max_length=254, blank=True, verbose_name="Email del Conductor (opcional)")

    # Internal notes
    internal_notes = models.TextField(blank=True, verbose_name="Notas Internas",
                                      help_text="Observaciones sobre el vehículo (seguro, mantención, etc.)")

    class Meta:
        db_table = "logistics_vehicle"
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['owner_company', 'plate']

    def __str__(self):
        return f"{self.plate} — {self.owner_company} (Cap: {self.capacity})"

    @property
    def contact_phone(self):
        """Returns driver_phone from direct field, or from linked default_driver if available."""
        if self.driver_phone:
            return self.driver_phone
        if self.default_driver and hasattr(self.default_driver, 'phone'):
            return getattr(self.default_driver, 'phone', '')
        return ''

    @property
    def contact_name(self):
        if self.driver_name:
            return self.driver_name
        if self.default_driver:
            return self.default_driver.get_full_name() or self.default_driver.username
        return '—'

    def build_whatsapp_message(self, stop):
        """Build a WhatsApp message for this vehicle's driver about a specific SaleTour stop."""
        from sales.models import SaleTour
        sale = stop.sale
        tour_name = stop.tour.name if stop.tour else 'Tour Privado'
        date_str  = stop.tour_date.strftime('%d/%m/%Y') if stop.tour_date else '—'
        time_str  = stop.pickup_time.strftime('%H:%M') if stop.pickup_time else 'Por confirmar'
        hotel     = sale.hotel_address or '—'
        pax_line  = f"{stop.pax_adults} adulto{'s' if stop.pax_adults != 1 else ''}"
        if stop.pax_infants:
            pax_line += f" + {stop.pax_infants} infante{'s' if stop.pax_infants != 1 else ''}"
        passengers = list(sale.passengers.all())
        pax_names  = ', '.join(f"{p.first_name} {p.last_name}" for p in passengers[:6])
        if len(passengers) > 6:
            pax_names += f" y {len(passengers)-6} más"

        msg = (
            f"🚐 *GETAWAY CHILE — Asignación de Viaje*\n\n"
            f"Hola *{self.contact_name}*,\n"
            f"Se te ha asignado un viaje. Aquí los detalles:\n\n"
            f"📅 *Fecha:* {date_str}\n"
            f"🕐 *Hora de recogida:* {time_str}\n"
            f"📍 *Lugar de recogida:* {hotel}\n"
            f"🗺️ *Tour / Destino:* {tour_name}\n"
            f"👥 *Pasajeros ({pax_line}):*\n{pax_names}\n"
        )
        if stop.logistics_notes:
            msg += f"\n📝 *Notas:* {stop.logistics_notes}\n"
        msg += "\nCualquier duda contacta a Logística Getaway Chile. ¡Gracias!"
        return msg

class DailyOperation(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="operations")
    date = models.DateField()
    driver = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_driver_operations",
        limit_choices_to={'role': 'CONDUCTOR'},
        verbose_name="Conductor"
    )
    guide = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_guide_operations",
        limit_choices_to={'role': 'GUIA'},
        verbose_name="Guía"
    )
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="daily_operations",
        verbose_name="Vehículo"
    )
    status = models.CharField(
        max_length=20, 
        choices=OperationStatus.choices, 
        default=OperationStatus.PENDING,
        verbose_name="Estado Operativo"
    )
    notes = models.TextField(blank=True, verbose_name="Notas de Logística")
    
    # Traceability / Check-in
    check_in_at = models.DateTimeField(null=True, blank=True, verbose_name="Hora de Check-in (Inicio Vaje)")
    check_in_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="check_ins_made", verbose_name="Iniciado por")
    check_out_at = models.DateTimeField(null=True, blank=True, verbose_name="Hora de Check-out (Fin Viaje)")
    check_out_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="check_outs_made", verbose_name="Finalizado por")

    # Internal metrics
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "logistics_daily_operation"
        verbose_name = "Operación Diaria (Grupo Viaje)"
        verbose_name_plural = "Operaciones Diarias (Grupos Viaje)"
        ordering = ['date', 'tour__name']

    def __str__(self):
        return f"{self.date} - {self.tour.name} - Vehículo: {self.vehicle.plate if self.vehicle else 'Sin asignar'} ({self.get_status_display()})"

