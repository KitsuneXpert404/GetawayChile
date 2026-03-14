from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Quotas
    path('dashboard/', views.LogisticsHomeView.as_view(), name='logistics_dashboard'),
    path('gestion-cupos/', views.LogisticsQuotasManagerView.as_view(), name='logistics_quotas_manager'),
    path('gestion-cupos/base/<int:tour_id>/', views.TourBaseQuotaUpdateView.as_view(), name='logistics_base_quota_update'),
    path('operation/<int:tour_id>/<str:date>/', views.DailyOperationUpdateView.as_view(), name='logistics_operation_update'),
    path('availability/<int:tour_id>/<str:date>/', views.TourAvailabilityUpdateView.as_view(), name='logistics_availability_update'),
    path('reservations/<int:tour_id>/<str:date>/', views.TourReservationsDetailView.as_view(), name='logistics_reservations_list'),

    # Sales Operations Dashboard (Centro de Control)
    path('operaciones/', views.LogisticsDashboardView.as_view(), name='logistics_sales_ops'),

    # Vehicles CRUD
    path('vehiculos/', views.VehicleListView.as_view(), name='logistics_vehicle_list'),
    path('vehiculos/nuevo/', views.VehicleCreateView.as_view(), name='logistics_vehicle_create'),
    path('vehiculos/<int:pk>/', views.VehicleDetailView.as_view(), name='logistics_vehicle_detail'),
    path('vehiculos/editar/<int:pk>/', views.VehicleUpdateView.as_view(), name='logistics_vehicle_update'),
    path('vehiculos/eliminar/<int:pk>/', views.VehicleDeleteView.as_view(), name='logistics_vehicle_delete'),

    # Assignments (legacy — sale level)
    path('asignar-venta/<int:pk>/', views.SaleLogisticsUpdateView.as_view(), name='logistics_sale_assign'),
    # Per-stop logistics assignment
    path('asignar-stop/<int:sale_pk>/stop/<int:stop_pk>/', views.StopLogisticsUpdateView.as_view(), name='logistics_stop_assign'),

    # Trip logistics management (new logistics-only page)
    path('gestion-viajes/', views.TripManagementView.as_view(), name='logistics_trip_management'),
    
    # Vehicle occupancy map
    path('ocupacion-vehiculos/', views.VehicleOccupancyDashboardView.as_view(), name='logistics_vehicle_occupancy'),

    # Logistics sale detail (read-only, for logistics users)
    path('auditoria_venta/<int:pk>/', views.LogisticsSaleDetailView.as_view(), name='logistics_sale_detail'),
    # Logistics sale manage (full management: confirm, cancel, assign, notify, traceability)
    path('gestionar/<int:pk>/', views.LogisticsSaleManageView.as_view(), name='logistics_sale_manage'),

    # Field Operations (Guides and Conductors)
    path('mis-viajes/', views.FieldOperationsDashboardView.as_view(), name='field_operations_dashboard'),
    path('viajes/<int:pk>/check-in/', views.FieldOperationCheckInView.as_view(), name='field_operation_check_in'),
    path('viajes/<int:pk>/check-out/', views.FieldOperationCheckOutView.as_view(), name='field_operation_check_out'),
]

