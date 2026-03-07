# Generated manually for Getaway Chile ERP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tour",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("tour_type", models.CharField(choices=[("REGULAR", "Tour Regular"), ("PRIVADO", "Tour Privado")], default="REGULAR", max_length=10)),
                ("precio_clp", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("precio_usd", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("precio_brl", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("dias_operativos", models.CharField(default="1,2,3,4,5,6", help_text="Días que opera: 0=Dom, 1=Lun, ..., 6=Sab. Ej: 1,3,5 para Lun,Mie,Vie", max_length=50)),
                ("cupo_maximo_diario", models.PositiveIntegerField(default=20, help_text="Stock máximo por día")),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "catalog_tour", "verbose_name": "Tour", "verbose_name_plural": "Tours", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="TourAvailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateField()),
                ("cupo_maximo", models.PositiveIntegerField(help_text="Puede sobrescribir el cupo por defecto del tour")),
                ("cupo_reservado", models.PositiveIntegerField(default=0)),
                ("tour", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availability", to="catalog.tour")),
            ],
            options={"db_table": "catalog_tour_availability", "verbose_name": "Disponibilidad de tour", "verbose_name_plural": "Disponibilidades", "ordering": ["fecha"], "unique_together": {("tour", "fecha")}},
        ),
    ]
