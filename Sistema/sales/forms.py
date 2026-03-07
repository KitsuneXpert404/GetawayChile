from django import forms
from django.forms import inlineformset_factory
from .models import Sale, Passenger
from catalog.models import Tour, TourAvailability
from django.core.exceptions import ValidationError
import datetime

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = [
            'client_first_name', 'client_last_name', 'client_rut_passport',
            'client_nationality', 'client_email', 'client_phone', 'hotel_address',
            'origin_channel', 'agency', 'currency',
            'payment_status', 'amount_paid', 'total_amount', 
            'voucher_image', 'voucher_image_2', 'voucher_image_3',
            'private_trip_description', 'private_trip_observations',
        ]
        widgets = {
            'tour_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'onkeydown': 'return false'}),
            'client_first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'client_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'client_rut_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'client_nationality': forms.Select(attrs={'class': 'form-control'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nombre@ejemplo.com'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 ...'}),
            'hotel_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección de recogida'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_private'}),
            'origin_channel': forms.Select(attrs={'class': 'form-select'}),
            'agency': forms.Select(attrs={'class': 'form-control'}),
            'tour': forms.Select(attrs={'class': 'form-control'}),
            'tour_language': forms.Select(attrs={'class': 'form-select'}),
            'passengers_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voucher_image': forms.FileInput(attrs={'class': 'form-control'}),
            'voucher_image_2': forms.FileInput(attrs={'class': 'form-control'}),
            'voucher_image_3': forms.FileInput(attrs={'class': 'form-control'}),
            'private_trip_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles del viaje a medida...'}),
            'private_trip_observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones internas o para el conductor...'}),
        }

    def clean(self):
        return super().clean()

PassengerFormSet = inlineformset_factory(
    Sale, Passenger,
    fields=['first_name', 'last_name', 'rut_passport', 'nationality'],
    widgets={
        'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
        'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
        'rut_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT/Pasaporte'}),
        'nationality': forms.Select(attrs={'class': 'form-select'}),
    },
    extra=1,
    can_delete=True
)

PassengerUpdateFormSet = inlineformset_factory(
    Sale, Passenger,
    fields=['first_name', 'last_name', 'rut_passport', 'nationality'],
    widgets={
        'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
        'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
        'rut_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT/Pasaporte'}),
        'nationality': forms.Select(attrs={'class': 'form-select'}),
    },
    extra=0,
    can_delete=True
)
