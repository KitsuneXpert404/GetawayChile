from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    # Optional field for manual password setting
    password_provisional = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para generar automática'}),
        label="Contraseña Provisoria (Opcional)"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'second_name', 'last_name', 'second_last_name', 
            'rut', 'phone', 'personal_email', 'birth_date', 'role',
            'password_provisional', 'photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'second_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Andrés'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pérez'}),
            'second_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'González'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9', 'id': 'rutInput', 'maxlength': '12'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'juan.perez@gmail.com'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer obligatorios los datos importantes
        required_fields = ['first_name', 'last_name', 'rut', 'phone', 'personal_email', 'birth_date']
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # === 1. Auto-generar Email Institucional ===
        # Formato: 3 primeras letras nombre . apellido_paterno @sistemagetawaychile.cl
        # Ej: ric.flores@sistemagetawaychile.cl
        first_name_clean = slugify(user.first_name.split()[0])
        first_part = first_name_clean[:3] # Primeras 3 letras
        last_name_clean = slugify(user.last_name.split()[0])
        
        base_email = f"{first_part}.{last_name_clean}@sistemagetawaychile.cl"
        email = base_email
        counter = 1
        
        # Validar si correo ya existe (Ej: hay dos Ricardo Flores -> ric.flores1)
        while User.objects.filter(email=email).exists():
            email = f"{first_part}.{last_name_clean}{counter}@sistemagetawaychile.cl"
            counter += 1
            
        user.email = email
        user.username = email
        
        # === 2. Lógica de Contraseña ===
        # Formato: Primera letra mayúscula del nombre + RUT limpio (sin guion ni puntos)
        password_input = self.cleaned_data.get('password_provisional')
        generated_password = ""
        
        if password_input:
             generated_password = password_input
        elif user.rut and user.first_name:
            # Limpiar RUT de puntos y guiones
            clean_rut = user.rut.replace('.', '').replace('-', '').lower()
            # Primera letra del nombre en mayúscula
            first_letter_name = user.first_name.strip()[0].upper()
            generated_password = f"{first_letter_name}{clean_rut}"
        else:
            generated_password = "Getaway2025!" # Respaldo default forzado si faltasen datos
            
        user.set_password(generated_password)
        # Forzar petición de cambio al ingresar
        user.requires_password_change = True
            
        if commit:
            user.save()
            
            # === 3. Enviar Correo de Bienvenida con Credenciales (Asíncrono) ===
            from django.core.mail import send_mail
            import logging
            import threading
            
            logger = logging.getLogger(__name__)
            
            def enviar_correo_bienvenida(user_obj, password):
                from django.conf import settings
                asunto = "Bienvenido al Equipo | Credenciales de Acceso Getaway Chile"
                mensaje = f"""Hola {user_obj.first_name},

¡Bienvenido al ERP de Getaway Chile!
Se ha creado tu perfil en el sistema corporativo con el rol de {user_obj.get_role_display()}.

A continuación, tus credenciales de acceso iniciales:

URL de Acceso: https://sistemagetawaychile.cl/dashboard/
Email / Usuario: {user_obj.email}
Contraseña Temporal: {password}

IMPORTANTE: 
1. Al iniciar sesión por primera vez, el sistema te exigirá que cambies esta contraseña provisoria por una definitiva por motivos de seguridad. 
2. Protege tu correo institucional y asegúrate de completar tus datos de perfil una vez que ingreses.

Saludos cordiales,
Equipo Administrativo de Getaway Chile.
"""
                try:
                    send_mail(
                        subject=asunto,
                        message=mensaje,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_obj.personal_email] if user_obj.personal_email else [],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Error enviando correo a usuario nuevo {user_obj.email}: {e}")

                # WhatsApp de Bienvenida
                try:
                    from notifications.whatsapp import _twilio_send, _normalize_phone
                    if user_obj.phone:
                        phone = _normalize_phone(user_obj.phone, 'Chilena') # Default Chile para empleados
                        if phone:
                            wa_body = (
                                f"👋 *¡Bienvenido al equipo de Getaway Chile!*\n\n"
                                f"Hola {user_obj.first_name}, tu cuenta de {user_obj.get_role_display()} "
                                f"ha sido activada exitosamente.\n\n"
                                f"🔑 *Tus credenciales:*\n"
                                f"• Email: {user_obj.email}\n"
                                f"• Contraseña Temporal: {password}\n\n"
                                f"Accede al sistema aquí: https://sistemagetawaychile.cl/login/\n\n"
                                f"⚠️ _El sistema te pedirá cambiar esta contraseña provisoria al ingresar por primera vez._"
                            )
                            # Passing None for sale, not needed just for twilio auth
                            _twilio_send(user_obj, phone, wa_body, 'ES')
                except Exception as wa_e:
                    logger.error(f"Error enviando WhatsApp a usuario nuevo {user_obj.email}: {wa_e}")

            # Lanzar el envío de correo en un hilo paralelo para no congelar la pantalla de creación
            email_thread = threading.Thread(target=enviar_correo_bienvenida, args=(user, generated_password))
            email_thread.daemon = True
            email_thread.start()
            
        return user

class CustomUserUpdateForm(forms.ModelForm):
    # Optional field for manual password setting (only if admin wants to force reset)
    password_provisional = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para mantener la actual'}),
        label="Nueva Contraseña (Opcional)"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'second_name', 'last_name', 'second_last_name', 
            'rut', 'phone', 'personal_email', 'birth_date', 'role', 'is_active', 'photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'second_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Andrés'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pérez'}),
            'second_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'González'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9', 'id': 'rutInput', 'maxlength': '12'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'juan.perez@gmail.com'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Only set password if provided
        password_input = self.cleaned_data.get('password_provisional')
        if password_input:
             user.set_password(password_input)
             user.requires_password_change = True # Require change if admin sets a new one
            
        if commit:
            user.save()
        return user
