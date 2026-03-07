from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "id",
            "nombre",
            "rut_pasaporte",
            "nacionalidad",
            "telefono",
            "email",
            "direccion_hotel",
            "contacto_emergencia_nombre",
            "contacto_emergencia_telefono",
            "created_at",
        )

    def validate_rut_pasaporte(self, value):
        value = (value or "").strip().upper()
        if not value:
            raise serializers.ValidationError("RUT/Pasaporte es obligatorio.")
        if self.instance is None and Client.objects.filter(rut_pasaporte=value).exists():
            raise serializers.ValidationError(
                "Ya existe un cliente con este RUT/Pasaporte."
            )
        return value
