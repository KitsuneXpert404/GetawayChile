from decimal import Decimal
from rest_framework import serializers
from catalog.models import Tour, TourType
from catalog.models import TourAvailability
from clients.models import Client
from users.models import CustomUser
from .models import Sale, SaleDetail, SalePassenger, Currency, PaymentStatus


class ClientMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "nombre", "rut_pasaporte", "email", "telefono", "direccion_hotel")


class SalePassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalePassenger
        fields = ("id", "nombre", "rut_pasaporte", "orden")


class SaleDetailSerializer(serializers.ModelSerializer):
    tour_name = serializers.CharField(source="tour.name", read_only=True)

    class Meta:
        model = SaleDetail
        fields = (
            "id",
            "tour",
            "tour_name",
            "tour_type",
            "fecha_tour",
            "descripcion_tour",
            "observaciones_cotizacion",
            "precio_unitario_clp",
            "precio_unitario_usd",
            "precio_unitario_brl",
            "cantidad_pasajeros",
            "moneda",
            "subtotal",
        )
        read_only_fields = ()


class SaleDetailForConductorSerializer(serializers.ModelSerializer):
    """Solo fecha y nombre/descripción del tour, sin precios."""
    tour_name = serializers.CharField(source="tour.name", read_only=True)

    class Meta:
        model = SaleDetail
        fields = ("id", "fecha_tour", "tour_name", "descripcion_tour", "cantidad_pasajeros")


class SaleForConductorSerializer(serializers.ModelSerializer):
    """Vista para conductor: sin precios, con pasajeros y dirección hotel."""
    cliente_nombre = serializers.CharField(source="cliente_principal.nombre", read_only=True)
    direccion_hotel = serializers.CharField(source="cliente_principal.direccion_hotel", read_only=True)
    pasajeros = SalePassengerSerializer(many=True, read_only=True)
    detalles = SaleDetailForConductorSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = ("id", "cliente_nombre", "direccion_hotel", "created_at", "pasajeros", "detalles")


class SaleListSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(
        source="cliente_principal.nombre", read_only=True
    )
    vendedor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = (
            "id",
            "cliente_principal",
            "cliente_nombre",
            "vendedor",
            "vendedor_nombre",
            "moneda_pago",
            "monto_total",
            "monto_pagado",
            "estado_pago",
            "estado_venta",
            "sobrecupo",
            "created_at",
        )

    def get_vendedor_nombre(self, obj):
        return obj.vendedor.get_full_name() or obj.vendedor.username


class SaleCreateUpdateSerializer(serializers.ModelSerializer):
    detalles = SaleDetailSerializer(many=True)
    pasajeros = SalePassengerSerializer(many=True)

    class Meta:
        model = Sale
        fields = (
            "id",
            "cliente_principal",
            "moneda_pago",
            "monto_total",
            "monto_pagado",
            "estado_pago",
            "voucher",
            "sobrecupo",
            "detalles",
            "pasajeros",
        )

    def validate(self, data):
        if not data.get("voucher") and not self.instance:
            raise serializers.ValidationError(
                {"voucher": "El comprobante/voucher es obligatorio."}
            )
        detalles = data.get("detalles", [])
        if not detalles:
            raise serializers.ValidationError(
                {"detalles": "Debe incluir al menos un detalle (tour o experiencia)."}
            )
        pasajeros = data.get("pasajeros", [])
        if not pasajeros:
            raise serializers.ValidationError(
                {"pasajeros": "Debe incluir al menos un pasajero."}
            )
        total_calc = Decimal("0")
        for d in detalles:
            if d["tour_type"] == TourType.REGULAR:
                if not d.get("tour"):
                    raise serializers.ValidationError(
                        {"detalles": "Tour regular debe tener tour asociado."}
                    )
                if not d.get("fecha_tour"):
                    raise serializers.ValidationError(
                        {"detalles": "Tour regular debe tener fecha."}
                    )
            else:
                if not (d.get("descripcion_tour") or "").strip():
                    raise serializers.ValidationError(
                        {"detalles": "Tour privado requiere descripción."}
                    )
            total_calc += d["subtotal"]
        if data.get("monto_total") is not None and abs(data["monto_total"] - total_calc) > Decimal("0.01"):
            data["monto_total"] = total_calc
        data["monto_total"] = total_calc
        return data

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        pasajeros_data = validated_data.pop("pasajeros")
        validated_data["vendedor"] = self.context["request"].user
        validated_data.setdefault("estado_venta", "SOLICITADA")
        sale = Sale.objects.create(**validated_data)
        for i, d in enumerate(detalles_data):
            detail = SaleDetail.objects.create(sale=sale, **d)
            if detail.tour and detail.fecha_tour and detail.tour_type == TourType.REGULAR:
                avail, _ = TourAvailability.objects.get_or_create(
                    tour=detail.tour,
                    fecha=detail.fecha_tour,
                    defaults={"cupo_maximo": detail.tour.cupo_maximo_diario},
                )
                avail.cupo_reservado += detail.cantidad_pasajeros
                avail.save(update_fields=["cupo_reservado"])
        for i, p in enumerate(pasajeros_data):
            p["orden"] = i + 1
            SalePassenger.objects.create(sale=sale, **p)
        return sale

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop("detalles", None)
        pasajeros_data = validated_data.pop("pasajeros", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if detalles_data is not None:
            instance.detalles.all().delete()
            for d in detalles_data:
                SaleDetail.objects.create(sale=instance, **d)
        if pasajeros_data is not None:
            instance.pasajeros.all().delete()
            for i, p in enumerate(pasajeros_data):
                p["orden"] = i + 1
                SalePassenger.objects.create(sale=instance, **p)
        return instance


class SaleDetailWriteSerializer(serializers.Serializer):
    tour = serializers.PrimaryKeyRelatedField(
        queryset=Tour.objects.filter(active=True), required=False, allow_null=True
    )
    tour_type = serializers.ChoiceField(choices=TourType.choices)
    fecha_tour = serializers.DateField(required=False, allow_null=True)
    descripcion_tour = serializers.CharField(required=False, allow_blank=True)
    observaciones_cotizacion = serializers.CharField(required=False, allow_blank=True)
    cantidad_pasajeros = serializers.IntegerField(min_value=1, default=1)
    moneda = serializers.ChoiceField(choices=Currency.choices)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    precio_unitario_clp = serializers.DecimalField(
        max_digits=12, decimal_places=0, required=False, allow_null=True
    )
    precio_unitario_usd = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    precio_unitario_brl = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )


class SaleWriteSerializer(serializers.Serializer):
    cliente_principal = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    moneda_pago = serializers.ChoiceField(choices=Currency.choices)
    monto_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    monto_pagado = serializers.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0")
    )
    estado_pago = serializers.ChoiceField(
        choices=PaymentStatus.choices, default=PaymentStatus.PENDIENTE
    )
    voucher = serializers.FileField(allow_null=False)
    sobrecupo = serializers.BooleanField(default=False)
    detalles = SaleDetailWriteSerializer(many=True)
    pasajeros = SalePassengerSerializer(many=True)

    def validate(self, data):
        if not data.get("pasajeros"):
            raise serializers.ValidationError(
                {"pasajeros": "Debe incluir al menos un pasajero."}
            )
        total = sum(d["subtotal"] for d in data["detalles"])
        data["monto_total"] = total
        return data

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        pasajeros_data = validated_data.pop("pasajeros")
        validated_data["vendedor"] = self.context["request"].user
        validated_data.setdefault("estado_venta", "SOLICITADA")
        sale = Sale.objects.create(**validated_data)
        for d in detalles_data:
            detail = SaleDetail.objects.create(sale=sale, **d)
            if detail.tour and detail.fecha_tour and detail.tour_type == TourType.REGULAR:
                avail, _ = TourAvailability.objects.get_or_create(
                    tour=detail.tour,
                    fecha=detail.fecha_tour,
                    defaults={"cupo_maximo": detail.tour.cupo_maximo_diario},
                )
                avail.cupo_reservado += detail.cantidad_pasajeros
                avail.save(update_fields=["cupo_reservado"])
        for i, p in enumerate(pasajeros_data):
            SalePassenger.objects.create(sale=sale, orden=i + 1, **p)
        return sale
