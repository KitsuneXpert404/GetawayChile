from django import forms
from .models import Ticket, TicketType, TargetRole
from catalog.models import Tour


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['target_role', 'ticket_type', 'title', 'description', 'tour', 'tour_date']
        widgets = {
            'target_role': forms.Select(attrs={'class': 'form-select'}),
            'ticket_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Describe brevemente el asunto'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detalla tu solicitud...'}),
            'tour': forms.Select(attrs={'class': 'form-select'}),
            'tour_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tour'].queryset = Tour.objects.filter(active=True).order_by('name')
        self.fields['tour'].required = False
        self.fields['tour_date'].required = False


class TicketRespondForm(forms.Form):
    response = forms.CharField(
        label='Respuesta',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe tu respuesta aquí...'}),
        required=True,
    )
    new_status = forms.ChoiceField(
        label='Cambiar Estado',
        choices=[
            ('EN_REVISION', 'Marcar En Revisión'),
            ('APROBADA', 'Aprobar Solicitud'),
            ('RECHAZADA', 'Rechazar Solicitud'),
            ('CERRADA', 'Cerrar Ticket'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
