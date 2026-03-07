from django import forms
from .models import Tour, TourType

# Regiones de Chile (incluye Aysén con tilde correcta)
REGIONES_CHILE = [
    ('', 'Seleccione región...'),
    ('Arica y Parinacota', 'Arica y Parinacota'),
    ('Tarapacá', 'Tarapacá'),
    ('Antofagasta', 'Antofagasta'),
    ('Atacama', 'Atacama'),
    ('Coquimbo', 'Coquimbo'),
    ('Valparaíso', 'Valparaíso'),
    ('Metropolitana de Santiago', 'Metropolitana de Santiago'),
    ("O'Higgins", "O'Higgins"),
    ('Maule', 'Maule'),
    ('Ñuble', 'Ñuble'),
    ('Biobío', 'Biobío'),
    ('La Araucanía', 'La Araucanía'),
    ('Los Ríos', 'Los Ríos'),
    ('Los Lagos', 'Los Lagos'),
    ('Aysén', 'Aysén'),
    ('Magallanes', 'Magallanes'),
]


class TourForm(forms.ModelForm):
    LANGUAGE_CHOICES = [
        ('Español', 'Español'),
        ('Inglés', 'Inglés'),
        ('Portugués', 'Portugués'),
    ]

    DIAS_CHOICES = [
        ('1', 'Lunes'),
        ('2', 'Martes'),
        ('3', 'Miércoles'),
        ('4', 'Jueves'),
        ('5', 'Viernes'),
        ('6', 'Sábado'),
        ('0', 'Domingo'),
    ]

    languages_selection = forms.MultipleChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Idiomas Disponibles"
    )

    other_languages = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Japonés, Mandarín'}),
        label="Otros Idiomas"
    )

    dias_operativos_selection = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Días Operativos"
    )

    region = forms.ChoiceField(
        choices=REGIONES_CHILE,
        required=False,
        label="Región de Origen",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Tour
        fields = [
            'name', 'tour_type', 'destination', 'region',
            'duration', 'cupo_maximo_diario',
            'precio_clp', 'precio_adulto_clp', 'precio_infante_clp',
            'precio_usd', 'precio_adulto_usd', 'precio_infante_usd',
            'precio_brl', 'precio_adulto_brl', 'precio_infante_brl',
            'includes', 'not_includes', 'description',
            'image_1', 'image_2', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Tour'}),
            'tour_type': forms.Select(attrs={'class': 'form-select'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: San Pedro de Atacama'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 08 - 10 horas'}),
            'cupo_maximo_diario': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_clp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'precio_adulto_clp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'precio_infante_clp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'precio_usd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'precio_adulto_usd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'precio_infante_usd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'precio_brl': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'precio_adulto_brl': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'precio_infante_brl': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'includes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'not_includes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image_1': forms.FileInput(attrs={'class': 'form-control'}),
            'image_2': forms.FileInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('active', False)

        # Languages Logic
        selected_langs = cleaned_data.get('languages_selection', [])
        other_langs = cleaned_data.get('other_languages')

        final_langs = list(selected_langs)
        if other_langs:
            others = [lang.strip() for lang in other_langs.split(',') if lang.strip()]
            final_langs.extend(others)

        if final_langs:
            self.instance.languages = ", ".join(final_langs)
        elif is_active:
            self.add_error('languages_selection', "Debe seleccionar al menos un idioma si el tour está activo.")

        # Days Logic
        selected_days = cleaned_data.get('dias_operativos_selection', [])
        if selected_days:
            self.instance.dias_operativos = ",".join(selected_days)
        elif is_active:
            self.add_error('dias_operativos_selection', "Debe seleccionar al menos un día operativo si el tour está activo.")
        else:
            self.instance.dias_operativos = ""

        # Validate required fields for Active tours
        if is_active:
            if not cleaned_data.get('precio_clp') and not cleaned_data.get('precio_adulto_clp'):
                self.add_error('precio_clp', "El precio base o precio adulto CLP es obligatorio para activar el tour.")
            if not cleaned_data.get('includes'):
                self.add_error('includes', "Debe especificar qué incluye el tour.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-populate Languages
        if self.instance and self.instance.pk and self.instance.languages:
            current_langs = [la.strip() for la in self.instance.languages.split(',')]
            valid_choices = [c[0] for c in self.LANGUAGE_CHOICES]

            initial_selection = []
            initial_other = []

            for lang in current_langs:
                if lang in valid_choices:
                    initial_selection.append(lang)
                else:
                    initial_other.append(lang)

            self.fields['languages_selection'].initial = initial_selection
            self.fields['other_languages'].initial = ", ".join(initial_other)

        # Pre-populate Days
        if self.instance and self.instance.pk and self.instance.dias_operativos:
            current_days = [d.strip() for d in self.instance.dias_operativos.split(',')]
            self.fields['dias_operativos_selection'].initial = current_days
        elif not self.instance.pk:
            self.fields['dias_operativos_selection'].initial = ['1', '2', '3', '4', '5', '6']
