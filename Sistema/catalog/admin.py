from django.contrib import admin
from .models import Tour, TourAvailability


class TourAvailabilityInline(admin.TabularInline):
    model = TourAvailability
    extra = 0
    fields = ("fecha", "cupo_maximo", "cupo_reservado")


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("name", "tour_type", "precio_clp", "precio_usd", "cupo_maximo_diario", "active")
    list_filter = ("tour_type", "active")
    search_fields = ("name",)
    inlines = [TourAvailabilityInline]


@admin.register(TourAvailability)
class TourAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("tour", "fecha", "cupo_maximo", "cupo_reservado")
    list_filter = ("tour", "fecha")
    date_hierarchy = "fecha"
