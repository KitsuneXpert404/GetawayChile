from rest_framework import serializers
from .models import Tour, TourAvailability, TourType


class TourSerializer(serializers.ModelSerializer):
    tour_type_display = serializers.CharField(
        source="get_tour_type_display", read_only=True
    )

    class Meta:
        model = Tour
        fields = (
            "id",
            "name",
            "tour_type",
            "tour_type_display",
            "precio_clp",
            "precio_usd",
            "precio_brl",
            "dias_operativos",
            "cupo_maximo_diario",
            "active",
            "created_at",
        )
        read_only_fields = fields


class TourAvailabilitySerializer(serializers.ModelSerializer):
    cupo_disponible = serializers.IntegerField(read_only=True)

    class Meta:
        model = TourAvailability
        fields = (
            "id",
            "tour",
            "fecha",
            "cupo_maximo",
            "cupo_reservado",
            "cupo_disponible",
        )
