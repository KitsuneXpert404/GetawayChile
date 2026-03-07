# Getaway Chile - ERP

Sistema interno de gestión para la agencia de turismo Getaway Chile. Backend en Django 5 + DRF, frontend en Next.js 14 con TypeScript, Tailwind y Shadcn/UI.

## Requisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL (opcional; por defecto se usa SQLite en desarrollo)

## Backend (Django)

```bash
cd Sistema
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

Crear archivo `.env` en `Sistema/` (opcional; ver `.env.example`). Para usar PostgreSQL:

```
USE_POSTGRES=true
PG_DATABASE=getaway_chile
PG_USER=postgres
PG_PASSWORD=postgres
PG_HOST=localhost
PG_PORT=5432
```

Aplicar migraciones y crear superusuario:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Ejecutar servidor:

```bash
python manage.py runserver
```

API disponible en `http://localhost:8000/api/`. Documentación de tokens JWT:

- `POST /api/auth/token/` — body: `{"username","password"}` → `{"access","refresh"}`
- `POST /api/auth/token/refresh/` — body: `{"refresh"}` → `{"access"}`
- `GET /api/auth/users/me/` — cabecera: `Authorization: Bearer <access>`

## Frontend (Next.js)

```bash
cd Sistema/frontend
npm install
```

Crear `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Ejecutar en desarrollo:

```bash
npm run dev
```

Abrir `http://localhost:3000`. Iniciar sesión con el usuario creado en Django.

## Estructura del proyecto

- **Backend**: `config/` (settings, URLs), `users/`, `catalog/`, `clients/`, `sales/`, `logistics/`
- **Frontend**: `app/` (App Router), `components/` (ui, layout, sales con SalesWizard), `lib/`, `hooks/`, `types/`

## Dashboards por rol

Cada usuario entra a su propio dashboard según su rol:

| Rol | Dashboard | Contenido |
|-----|-----------|-----------|
| **Admin** | `/dashboard/admin` | KPIs globales, ranking de vendedores, todas las ventas |
| **Vendedor** | `/dashboard/vendedor` | Mis ventas, mis KPIs, última ventas del período |
| **Logística** | `/dashboard/logistica` | Ventas pendientes de confirmar, enlace a panel logística |
| **Conductor** | `/dashboard/conductor` | Viajes asignados (calendario/rutas) |
| **Desarrollador** | `/dashboard/desarrollador` | Vista de soporte, sin datos sensibles |

Al iniciar sesión se redirige automáticamente a la ruta correspondiente. El menú lateral muestra solo las opciones permitidas para cada rol.

## Colores de marca

La interfaz usa la paleta de Getaway Chile: **teal** (azul verdoso oscuro) como color principal y **naranja óxido** como acento (slogan “Turismo y transporte”). Definidos en `frontend/app/globals.css`.

## Despliegue en Render

1. **Conectar el repositorio** en [Render](https://render.com). Si el repo tiene la carpeta `Sistema` en la raíz, en cada servicio configura **Root Directory** en Settings:
   - Backend: `Sistema`
   - Frontend: `Sistema/frontend`

2. **Crear un Blueprint** (New > Blueprint) y usar el archivo `render.yaml` de este proyecto, o crear los servicios a mano:

   **Base de datos**
   - New > PostgreSQL. Anotar la **Internal Database URL** (o Connection String).

   **Backend (Web Service)**
   - Runtime: Python  
   - Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`  
   - Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`  
   - Variables de entorno:
     - `DJANGO_SECRET_KEY`: generar valor aleatorio
     - `DATABASE_URL`: pegar la URL de la base PostgreSQL de Render
     - `DEBUG`: `false`
     - `ALLOWED_HOSTS`: `.onrender.com`
     - `CORS_ORIGINS`: URL del frontend en Render (ej. `https://getaway-chile-app.onrender.com`)

   **Frontend (Web Service)**
   - Runtime: Node  
   - Build: `npm install && npm run build`  
   - Start: `npm start`  
   - Variable de entorno:
     - `NEXT_PUBLIC_API_URL`: URL del backend + `/api` (ej. `https://getaway-chile-api.onrender.com/api`)

3. Tras el primer deploy del backend, crear un superusuario desde **Shell** en Render:  
   `python manage.py createsuperuser`

## Flujo principal

1. **Login** — Glassmorphism, colores Getaway Chile; JWT guardado en `localStorage`.
2. **Dashboard** — Redirige por rol (admin, vendedor, logística, conductor, desarrollador).
3. **Nueva venta (Wizard)** — 4 pasos: Cliente (búsqueda RUT / crear nuevo), Experiencia (Regular con calendario/cupos o Privado con descripción y precio), Pasajeros, Cierre y pago (voucher, términos).
4. **Logística** — Listado de ventas solicitadas; confirmar y asignar conductor.
5. **CRUDs** — Ventas, clientes, tours (listado y detalle).
