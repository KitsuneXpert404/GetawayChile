# Análisis y mejoras — ERP Getaway Chile (V2.0)

Documento de análisis del sistema web, mejoras de seguridad, sistema, animaciones y limpieza de código para los roles **ADMIN**, **VENDEDOR** y **LOGISTICA**.

---

## 1. Resumen del sistema

El ERP es una **plataforma web interna** (Django + templates HTML) para la agencia Getaway Chile. No hay frontend en Next.js en este repositorio; la interfaz se sirve desde Django.

| Componente | Tecnología |
|------------|------------|
| Backend | Django + PostgreSQL (Render) |
| Frontend | Templates Django (HTML/CSS/JS) |
| Almacenamiento | Cloudinary (vouchers) |
| Auth web | Sesión Django + CSRF |
| API REST | DRF + JWT (Simple JWT) |

**Roles:** Desarrollador, ADMIN (dueño), LOGISTICA, VENDEDOR, CONDUCTOR. Cada rol tiene una base de layout distinta (`base_dashboard`, `base_vendedor`, `base_logistica`, `base_conductor`) y vistas filtradas por permisos.

---

## 2. Mejoras de seguridad (aplicadas y recomendadas)

### 2.1 Aplicadas en este análisis

| Medida | Descripción |
|--------|-------------|
| **Endpoints de ventas protegidos** | `get_tour_details` y `check_availability` ahora exigen `@login_required`. Antes cualquier persona podía consultar precios, días operativos y disponibilidad. |
| **Exportación Excel restringida** | `export_sales_excel` solo permite acceso a usuarios con rol ADMIN o LOGISTICA. Cualquier otro usuario recibe 403. |
| **API de clientes por rol** | Se añadió el permiso `IsAdminOrLogisticaOrReadOnly`: cualquier usuario autenticado puede **listar y consultar** clientes (para el formulario de ventas); **crear, editar y eliminar** solo ADMIN y LOGISTICA. |

### 2.2 Recomendaciones adicionales

- **Rate limiting:** Añadir límite de peticiones por IP/usuario en `api/tour-details/`, `api/check-availability/` y en login para mitigar abuso y scraping.
- **Auditoría:** Registrar en logs (o modelo de auditoría) acciones sensibles: export Excel, eliminación de ventas, cambios de estado, gestión de usuarios.
- **CORS:** Revisar que `CORS_ALLOWED_ORIGINS` en producción solo incluya el dominio real de la app (y no `*`).
- **Sanitización:** Mantener el autoescape de Django en templates; en cualquier campo que permita HTML (si se añade en el futuro) usar una librería de sanitización (ej. `bleach`).
- **Vendedor y creación de clientes:** Si el flujo de ventas requiere que el VENDEDOR **cree** clientes por API, hay que ampliar el permiso (por ejemplo, permitir POST en clientes para rol VENDEDOR) o exponer un endpoint específico “crear cliente desde venta” con validaciones acotadas.

---

## 3. Mejoras del sistema por rol

### 3.1 ADMIN

- **Centralizar mixins de permisos:** Hoy existen varias definiciones de “solo admin” o “admin o logística” en `users/views_admin.py`, `core/views_reports.py`, `core/views_history.py`, `catalog/views.py`, `clients/views_agency.py`, `logistics/views.py`. Se recomienda crear un módulo único, por ejemplo `core.mixins` o `users.mixins`, con:
  - `AdminRequiredMixin` (solo ADMIN/DESARROLLADOR)
  - `AdminOrLogisticsRequiredMixin` (ADMIN o LOGISTICA)
  - y usarlos en todas las vistas que hoy duplican la lógica.
- **Reportes:** El mixin en `core/views_reports.py` ya permite ADMIN y LOGISTICA; mantener coherencia con el resto del sistema (mismo nombre de mixin y misma regla).
- **Logging:** Añadir logging (por ejemplo `logging.info`) en export Excel, eliminación de ventas y gestión de usuarios para trazabilidad.

### 3.2 VENDEDOR

- **Ventas:** Las vistas de ventas ya filtran por `seller=request.user` cuando el rol es VENDEDOR; el bug de `form.fields['total_amount']` en la edición de ventas (se usaba `form.fields[field]` por error) está corregido.
- **Tickets:** Revisar que los tickets creados por el vendedor solo muestren los suyos y que no pueda ver tickets de otros roles si no está permitido por negocio.
- **Cupos:** Si el vendedor accede a “gestión de cupos” (`LogisticsQuotasManagerView`), dejar documentado si es intencional (solo lectura) o si debe quitarse ese acceso.

### 3.3 LOGISTICA

- **Mismas vistas que ADMIN en reportes/historial/catálogo/agencias:** Usar los mixins centralizados (AdminOrLogisticsRequiredMixin) para no duplicar lógica.
- **Operaciones diarias y asignaciones:** Mantener la restricción actual (solo ADMIN y LOGISTICA) en vistas de logística.
- **Export Excel:** Ya puede exportar ventas; no requiere cambios adicionales si el negocio lo considera correcto.

---

## 4. Animaciones y UX

### 4.1 Estado actual

- Los bases (`base_dashboard.html`, `base_vendedor.html`, `base_logistica.html`, `base_conductor.html`) definen variables CSS (teal, gold, smoke) y transiciones cortas (ej. `transition: background 0.2s ease`).
- Hay animaciones como `gcFadeIn` / `fadeIn` en algunos templates; están definidas en bloques `<style>` inline repartidos entre archivos.

### 4.2 Recomendaciones

- **CSS común:** Extraer variables y animaciones compartidas a un archivo estático, por ejemplo `static/css/theme.css` o `static/css/animations.css`, y cargarlo desde `base.html` o desde cada `base_*.html`. Así se evita duplicar el mismo bloque en cuatro bases.
- **Animaciones consistentes:**
  - Entrada de páginas: una sola clase, por ejemplo `.gc-page-enter { animation: gcFadeIn 0.25s ease; }`.
  - Botones y enlaces: ya tienen `transition`; se puede unificar duración (ej. `0.2s`) y easing.
  - Listas y cards: aplicar una animación suave de aparición (ej. `opacity` + `transform`) en listados de ventas, usuarios, tours.
- **Feedback visual:** En formularios (ventas, usuarios, catálogo), mantener o añadir mensajes de éxito/error con una breve animación (ej. slide-in o fade) para que el usuario vea que la acción se registró.
- **Carga:** En vistas que puedan ser lentas (reportes, export Excel), considerar un indicador de “Procesando…” o deshabilitar el botón hasta que responda el servidor.

---

## 5. Limpieza de código

### 5.1 Corregido en este análisis

| Archivo | Cambio |
|---------|--------|
| `core/views.py` | Eliminado el bloque “Fallback” inalcanzable (líneas 110–112) que estaba después del `return` del diccionario en `_vendedor_context()`. |
| `sales/views.py` | En `SaleUpdateView.get_form()`, para el rol VENDEDOR se usaba `form.fields[field]` para marcar `total_amount` como readonly; `field` quedaba con el último valor del bucle. Corregido a `form.fields['total_amount']`. |

### 5.2 Recomendaciones de limpieza

- **Mixins:** Centralizar en un solo módulo (p. ej. `core/mixins.py`) y reemplazar todas las definiciones locales de `AdminRequiredMixin` y `AdminOrLogisticsRequiredMixin` por imports desde ese módulo. En `catalog/views.py` el mixin se llama “AdminRequiredMixin” pero en realidad permite ADMIN o LOGISTICA; conviene renombrarlo a `AdminOrLogisticsRequiredMixin` al centralizar.
- **Constantes:** `MESES_ES` y `DIAS_ES` en `core/views.py` se pueden mover a un módulo `core/constants.py` si se reutilizan en otros lugares.
- **Manejo de errores en API:** Unificar el formato de respuestas de error (JSON) en vistas que devuelven `JsonResponse` (por ejemplo `{"error": "mensaje"}` y código HTTP consistente) y documentarlo para el frontend.
- **Imports:** Evitar imports dentro de funciones donde no aporten (ej. `import datetime` dentro de `get_context_data`); moverlos al inicio del archivo.
- **Tests:** Añadir pruebas unitarias o de integración para:
  - Permisos por rol (export Excel, API clientes, get_tour_details, check_availability).
  - Filtrado de ventas por vendedor.
  - Que usuarios no autorizados reciban 403 en las rutas restringidas.

---

## 6. Resumen por rol (checklist)

| Área | ADMIN | VENDEDOR | LOGISTICA |
|------|--------|----------|-----------|
| **Seguridad** | Export Excel y APIs sensibles restringidos; revisar CORS y rate limit. | No accede a export ni a CRUD de usuarios; solo sus ventas. | No gestiona usuarios; sí reportes y operaciones. |
| **Sistema** | Centralizar mixins, logging en acciones críticas. | Verificar tickets y acceso a cupos según negocio. | Usar mismos mixins que admin en reportes/catálogo. |
| **Animaciones** | Unificar en CSS común y mismas clases en todos los roles. | Igual. | Igual. |
| **Código** | Eliminar duplicación de mixins y constantes. | Bug de `total_amount` en edición corregido. | Reutilizar mixins centralizados. |

---

## 7. Archivos clave modificados

- `core/views.py`: eliminado código muerto en `_vendedor_context`; añadida restricción por rol en `export_sales_excel`.
- `sales/views.py`: `@login_required` en `get_tour_details` y `check_availability`; corrección de `form.fields['total_amount']` en `SaleUpdateView`.
- `clients/views.py`: `permission_classes = [IsAdminOrLogisticaOrReadOnly]` en `ClientList` y `ClientDetail`.
- `users/permissions.py`: nuevo permiso `IsAdminOrLogisticaOrReadOnly` para la API de clientes.

---

*Documento generado a partir del análisis del código del ERP Getaway Chile. Ajustar recomendaciones según políticas internas y evolución del producto.*
