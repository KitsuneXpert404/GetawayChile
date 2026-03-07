# Generated manually for Getaway Chile ERP

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=200)),
                ("rut_pasaporte", models.CharField(db_index=True, max_length=20, unique=True)),
                ("nacionalidad", models.CharField(max_length=3)),
                ("telefono", models.CharField(max_length=30)),
                ("email", models.EmailField(max_length=254)),
                ("direccion_hotel", models.CharField(max_length=300)),
                ("contacto_emergencia_nombre", models.CharField(max_length=200)),
                ("contacto_emergencia_telefono", models.CharField(max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "clients_client", "verbose_name": "Cliente", "verbose_name_plural": "Clientes", "ordering": ["nombre"]},
        ),
    ]
