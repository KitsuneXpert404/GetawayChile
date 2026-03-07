from rest_framework import serializers
from sales.models import Sale
from sales.serializers import SaleListSerializer, SaleDetailSerializer, SalePassengerSerializer
from users.models import CustomUser
from .models import SaleLogistics, EstadoViaje


class SaleLogisticsSerializer(serializers.ModelSerializer):
    sale_data = SaleListSerializer(source="sale", read_only=True)

    class Meta:
        model = SaleLogistics
        fields = (
            "id",
            "sale",
            "sale_data",
            "estado_viaje",
            "comision",
            "conductor",
            "confirmado_at",
            "confirmado_por",
        )
        read_only_fields = ("confirmado_at", "confirmado_por")


class ConductorEstadoViajeSerializer(serializers.Serializer):
    estado_viaje = serializers.ChoiceField(choices=EstadoViaje.choices)


class SaleLogisticsConfirmSerializer(serializers.Serializer):
    conductor = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="CONDUCTOR"),
        required=False,
        allow_null=True,
    )


class SaleLogisticsComisionSerializer(serializers.Serializer):
    comision = serializers.DecimalField(max_digits=12, decimal_places=2)
