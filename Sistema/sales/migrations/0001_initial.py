# Generated manually for Getaway Chile ERP

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("clients", "0001_initial"),
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("moneda_pago", models.CharField(choices=[("CLP", "CLP"), ("USD", "USD"), ("BRL", "BRL")], max_length=3)),
                ("monto_total", models.DecimalField(decimal_places=2, max_digits=14)),
                ("monto_pagado", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("estado_pago", models.CharField(choices=[("PENDIENTE", "Pendiente"), ("ABONADO", "Abonado"), ("PAGADO", "Pagado")], default="PENDIENTE", max_length=20)),
                ("voucher", models.FileField(blank=True, upload_to="vouchers/%Y/%m/")),
                ("estado_venta", models.CharField(choices=[("SOLICITADA", "Solicitada"), ("CONFIRMADA", "Confirmada"), ("RECHAZADA", "Rechazada")], default="SOLICITADA", max_length=20)),
                ("sobrecupo", models.BooleanField(default=False, help_text="Vendido con cupo 0, pendiente aprobación logística")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cliente_principal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ventas", to="clients.client")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ventas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "sales_sale", "verbose_name": "Venta", "verbose_name_plural": "Ventas", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SaleDetail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tour_type", models.CharField(choices=[("REGULAR", "Tour Regular"), ("PRIVADO", "Tour Privado")], max_length=10)),
                ("fecha_tour", models.DateField(blank=True, null=True)),
                ("descripcion_tour", models.TextField(blank=True)),
                ("observaciones_cotizacion", models.TextField(blank=True)),
                ("precio_unitario_clp", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("precio_unitario_usd", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("precio_unitario_brl", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("cantidad_pasajeros", models.PositiveIntegerField(default=1)),
                ("moneda", models.CharField(choices=[("CLP", "CLP"), ("USD", "USD"), ("BRL", "BRL")], max_length=3)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=14)),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detalles", to="sales.sale")),
                ("tour", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ventas_detalle", to="catalog.tour")),
            ],
            options={"db_table": "sales_sale_detail", "verbose_name": "Detalle de venta", "verbose_name_plural": "Detalles de venta"},
        ),
        migrations.CreateModel(
            name="SalePassenger",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=200)),
                ("rut_pasaporte", models.CharField(max_length=20)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pasajeros", to="sales.sale")),
            ],
            options={"db_table": "sales_sale_passenger", "verbose_name": "Pasajero", "verbose_name_plural": "Pasajeros", "ordering": ["orden"]},
        ),
    ]
