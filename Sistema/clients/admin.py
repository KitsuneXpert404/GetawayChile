from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut_pasaporte", "nacionalidad", "email", "telefono")
    search_fields = ("nombre", "rut_pasaporte", "email")
    list_filter = ("nacionalidad",)
