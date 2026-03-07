from django import forms
from .models import DailyOperation, Vehicle
from catalog.models import TourAvailability
from users.models import CustomUser
from sales.models import Sale

class DailyOperationForm(forms.ModelForm):
    class Meta:
        model = DailyOperation
        fields = ['driver', 'notes', 'status']
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter drivers
        self.fields['driver'].queryset = CustomUser.objects.filter(role='CONDUCTOR', is_active=True)
        self.fields['driver'].label = "Conductor Asignado"
        self.fields['notes'].label = "Notas de Operación"
        self.fields['status'].label = "Estado del Viaje"


class TourAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TourAvailability
        fields = ['cupo_maximo']
        widgets = {
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'cupo_maximo': 'Cupo Máximo para esta Fecha'
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'plate', 'vehicle_type', 'vehicle_year', 'vehicle_color',
            'owner_company', 'capacity', 'is_active',
            'default_driver',
            'driver_name', 'driver_phone', 'driver_email',
            'internal_notes',
        ]
        widgets = {
            'plate':          forms.TextInput(attrs={'class': 'gc-input', 'placeholder': 'Ej. BCDF12'}),
            'vehicle_type':   forms.Select(attrs={'class': 'gc-input'}),
            'vehicle_year':   forms.NumberInput(attrs={'class': 'gc-input', 'placeholder': 'Ej. 2020', 'min': 1990, 'max': 2030}),
            'vehicle_color':  forms.TextInput(attrs={'class': 'gc-input', 'placeholder': 'Ej. Blanco'}),
            'owner_company':  forms.TextInput(attrs={'class': 'gc-input', 'placeholder': 'Nombre de agencia o dueño'}),
            'capacity':       forms.NumberInput(attrs={'class': 'gc-input', 'min': 1, 'max': 100}),
            'is_active':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_driver': forms.Select(attrs={'class': 'gc-input'}),
            'driver_name':    forms.TextInput(attrs={'class': 'gc-input', 'placeholder': 'Nombre completo del conductor'}),
            'driver_phone':   forms.TextInput(attrs={'class': 'gc-input', 'placeholder': '+56912345678', 'type': 'tel'}),
            'driver_email':   forms.EmailInput(attrs={'class': 'gc-input', 'placeholder': 'conductor@gmail.com'}),
            'internal_notes': forms.Textarea(attrs={'class': 'gc-input', 'rows': 3,
                                                    'placeholder': 'Seguro, mantención, observaciones...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import CustomUser
        self.fields['default_driver'].queryset = CustomUser.objects.filter(role='CONDUCTOR', is_active=True)
        self.fields['default_driver'].required = False
        self.fields['default_driver'].empty_label = '— Sin conductor del sistema —'

class SaleLogisticsForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['status', 'assigned_vehicle', 'pickup_time', 'logistics_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'assigned_vehicle': forms.Select(attrs={'class': 'form-select'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'logistics_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Anotaciones internas de logística...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(is_active=True)
        self.fields['status'].label = "Estado Logístico / Confirmación"
        
        # Ensure only Active vehicles are selectable for assignments.


class StopLogisticsForm(forms.ModelForm):
    """Form for assigning logistics to a single SaleTour stop."""
    class Meta:
        from sales.models import SaleTour
        model = SaleTour
        fields = ['assigned_vehicle', 'pickup_time', 'logistics_notes']
        widgets = {
            'assigned_vehicle': forms.Select(attrs={'class': 'form-select'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'logistics_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                     'placeholder': 'Notas internas para este stop...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(is_active=True)
        self.fields['assigned_vehicle'].label = "Vehículo / Agencia"
        self.fields['assigned_vehicle'].required = False
        self.fields['pickup_time'].label = "Hora de Recogida"
        self.fields['logistics_notes'].label = "Notas Internas (este stop)"
