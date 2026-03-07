from django.contrib import admin
from .models import Sale, Passenger

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_first_name', 'client_last_name', 'tour', 'tour_date', 'total_amount', 'payment_status')
    list_filter = ('payment_status', 'tour_date', 'tour')
    search_fields = ('client_first_name', 'client_last_name', 'client_rut_passport', 'id')
    inlines = [PassengerInline]

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'sale', 'rut_passport')
