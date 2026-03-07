from django.db import models
from simple_history.models import HistoricalRecords


class TourType(models.TextChoices):
    REGULAR = "REGULAR", "Tour Regular"
    PRIVADO = "PRIVADO", "Tour Privado"


class Tour(models.Model):
    name = models.CharField(max_length=200)
    tour_type = models.CharField(
        max_length=10, choices=TourType.choices, default=TourType.REGULAR
    )
    precio_clp = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="Precio Base CLP"
    )
    precio_adulto_clp = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="Precio Adulto CLP"
    )
    precio_infante_clp = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="Precio Infante CLP"
    )
    precio_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Base USD"
    )
    precio_adulto_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Adulto USD"
    )
    precio_infante_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Infante USD"
    )
    precio_brl = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Base BRL"
    )
    precio_adulto_brl = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Adulto BRL"
    )
    precio_infante_brl = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Infante BRL"
    )
    
    # New Fields
    destination = models.CharField(max_length=200, verbose_name="Destino", blank=True)
    region = models.CharField(max_length=200, verbose_name="Región de Origen", blank=True)
    
    # Description & Details
    description = models.TextField(verbose_name="Descripción Corta (Empleados)", blank=True)
    includes = models.TextField(verbose_name="Incluye", blank=True)
    not_includes = models.TextField(verbose_name="No Incluye", blank=True)
    duration = models.CharField(max_length=100, verbose_name="Duración (aprox)", help_text="Ej: 08 - 10 horas", blank=True)
    cancellation_policy = models.TextField(
        verbose_name="Políticas de Cancelación", 
        default="Cancelación gratuita hasta 48 horas antes del inicio del tour."
    )
    
    # Languages (Stored as text for now, simpler than M2M for MVP)
    languages = models.CharField(max_length=255, verbose_name="Idiomas Disponibles", help_text="Español, Inglés, etc.", blank=True)
    
    # Media
    image_1 = models.ImageField(upload_to='tours/', verbose_name="Foto Referencial 1", blank=True, null=True)
    image_2 = models.ImageField(upload_to='tours/', verbose_name="Foto Referencial 2", blank=True, null=True)

    dias_operativos = models.CharField(
        max_length=50,
        help_text="Días que opera: 0=Dom, 1=Lun, ..., 6=Sab. Ej: 1,3,5 para Lun,Mie,Vie",
        default="1,2,3,4,5,6",
    )
    cupo_maximo_diario = models.PositiveIntegerField(
        default=20, help_text="Stock máximo por día"
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "catalog_tour"
        verbose_name = "Tour"
        verbose_name_plural = "Tours"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_tour_type_display()})"

    def get_dias_list(self):
        if not self.dias_operativos:
            return []
        return [int(x.strip()) for x in self.dias_operativos.split(",")]


class TourAvailability(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="availability"
    )
    fecha = models.DateField()
    cupo_maximo = models.PositiveIntegerField(
        help_text="Puede sobrescribir el cupo por defecto del tour"
    )
    cupo_reservado = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "catalog_tour_availability"
        verbose_name = "Disponibilidad de tour"
        verbose_name_plural = "Disponibilidades"
        unique_together = [("tour", "fecha")]
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.tour.name} - {self.fecha}"

    @property
    def cupo_reservado_actual(self):
        # Dynamically calculate the reserved spots based on actual valid sales
        from sales.models import SaleTour
        from django.db.models import Sum
        
        total = SaleTour.objects.filter(
            tour=self.tour,
            tour_date=self.fecha,
        ).exclude(
            sale__status='CANCELADA' # Don't count cancelled sales
        ).aggregate(total_pax=Sum('sale__passengers_count'))['total_pax']
        
        return total or 0

    @property
    def cupo_disponible(self):
        return max(0, self.cupo_maximo - self.cupo_reservado_actual)
