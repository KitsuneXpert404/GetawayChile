from django import forms
from .models import Agency

class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'email', 'phone', 'contact_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la agencia'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@agencia.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 ...'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
        }
