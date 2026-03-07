# Squashed migration — replaces 0001 through 0005
# Final state: DailyOperation + Vehicle (SaleLogistics was created and deleted)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0004_add_adult_infant_pricing'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyOperation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(
                    choices=[('PENDIENTE', 'Pendiente'), ('CONFIRMADO', 'Confirmado'), ('REALIZADO', 'Realizado'), ('CANCELADO', 'Cancelado')],
                    default='PENDIENTE',
                    max_length=20,
                )),
                ('notes', models.TextField(blank=True, verbose_name='Notas de Logística')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role': 'CONDUCTOR'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_operations',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('tour', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='operations',
                    to='catalog.tour',
                )),
            ],
            options={
                'verbose_name': 'Operación Diaria',
                'verbose_name_plural': 'Operaciones Diarias',
                'db_table': 'logistics_daily_operation',
                'ordering': ['date', 'tour__name'],
                'unique_together': {('tour', 'date')},
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plate', models.CharField(max_length=20, unique=True, verbose_name='Patente / Placa')),
                ('owner_company', models.CharField(
                    help_text='Ej: Empresa XYZ o Juan Pérez',
                    max_length=150,
                    verbose_name='Dueño / Agencia',
                )),
                ('capacity', models.PositiveIntegerField(default=4, verbose_name='Capacidad de Pasajeros')),
                ('is_active', models.BooleanField(default=True, verbose_name='Vehículo Activo')),
                ('default_driver', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role': 'CONDUCTOR'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='default_vehicles',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Conductor por Defecto',
                )),
            ],
            options={
                'verbose_name': 'Vehículo',
                'verbose_name_plural': 'Vehículos',
                'db_table': 'logistics_vehicle',
                'ordering': ['owner_company', 'plate'],
            },
        ),
    ]
