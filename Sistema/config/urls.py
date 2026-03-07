from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")), # Frontend Routes
    path("dashboard/catalog/", include("catalog.urls")), # Catalog Routes
    path("dashboard/logistics/", include("logistics.urls")), # Logistics Routes
    path("api/auth/", include("users.urls")),
    path("api/", include("clients.urls")),
    path("dashboard/sales/", include("sales.urls")),
    path("notifications/", include("notifications.urls", namespace="notifications")),
    path("tickets/", include("tickets.urls", namespace="tickets")),
    # path("api/", include("logistics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
