# Deploy en Render — Getaway Chile ERP

Pasos para dejar el sistema listo y que los correos funcionen en producción.

## 1. Variables de entorno obligatorias en Render

En **Dashboard > Tu servicio > Environment** configura:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DEBUG` | Ya viene en blueprint: `false` | — |
| `ALLOWED_HOSTS` | Dominios permitidos | `.onrender.com` o `tu-app.onrender.com,sistema.getawaychile.cl` |
| `CSRF_TRUSTED_ORIGINS` | URLs con HTTPS para el sitio | `https://tu-app.onrender.com` |
| `EMAIL_HOST` | Servidor SMTP | `smtp.gmail.com` o `smtp.zoho.com` |
| `EMAIL_PORT` | Puerto SMTP | `587` |
| `EMAIL_USE_TLS` | Usar TLS | `true` |
| `EMAIL_HOST_USER` | Correo desde el que se envía | `sistema@getawaychile.cl` |
| `EMAIL_HOST_PASSWORD` | Contraseña (App Password en Google) | (valor secreto) |
| `DEFAULT_FROM_EMAIL` | Remitente visible en los correos | `Getaway Chile <sistema@getawaychile.cl>` |

**Google Workspace:** usa una [Contraseña de aplicación](https://support.google.com/accounts/answer/185833), no la contraseña normal del correo.

**Zoho Mail:** usa `EMAIL_HOST=smtp.zoho.com` y la contraseña de tu cuenta Zoho.

## 2. Después del primer deploy

1. Entra a la URL del servicio (ej. `https://tu-app.onrender.com`).
2. Inicia sesión con el usuario que definiste en `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD`.
3. Prueba **Restablecer contraseña** (en login) para comprobar que los correos se envían.
4. Crea un usuario de prueba desde **Dashboard > Usuarios** y revisa que llegue el correo de bienvenida al correo personal del usuario.

## 3. Cloudinary (vouchers e imágenes)

Si usas Cloudinary, añade la variable `CLOUDINARY_URL` (formato `cloudinary://api_key:secret@cloud_name`) en Environment. Sin ella, los archivos se guardan en el disco del servicio (se pierden en redeploys).

## 4. Comandos de build

El blueprint usa:

- **Build:** `./build.sh` (instala dependencias, `collectstatic`, `migrate`, `createsuperuser` si aplica).
- **Start:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`.

No es necesario configurar nada más para que los correos funcionen una vez definidas las variables de email.
