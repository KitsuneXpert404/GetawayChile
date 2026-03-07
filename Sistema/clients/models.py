from django.db import models


class Agency(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre de la Agencia")
    email = models.EmailField(blank=True, verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    contact_name = models.CharField(max_length=150, blank=True, verbose_name="Nombre de Contacto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clients_agency"
        verbose_name = "Agencia"
        verbose_name_plural = "Agencias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Client(models.Model):
    nombre = models.CharField(max_length=200)
    rut_pasaporte = models.CharField(max_length=20, unique=True, db_index=True)
    nacionalidad = models.CharField(max_length=3)  # ISO 3166-1 alpha-3
    telefono = models.CharField(max_length=30)
    email = models.EmailField()
    direccion_hotel = models.CharField(max_length=300)
    contacto_emergencia_nombre = models.CharField(max_length=200)
    contacto_emergencia_telefono = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_client"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rut_pasaporte})"
