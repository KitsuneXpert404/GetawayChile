from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='list'),
    path('crear/', views.SaleCreateView.as_view(), name='create'),
    path('ver/<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('editar/<int:pk>/', views.SaleUpdateView.as_view(), name='update'),
    path('eliminar/<int:pk>/', views.SaleDeleteView.as_view(), name='delete'),
    # Admin action endpoints
    path('confirmar/<int:pk>/', views.SaleConfirmView.as_view(), name='confirm'),
    path('cancelar/<int:pk>/', views.SaleCancelView.as_view(), name='cancel'),
    path('asignar-logistica/<int:pk>/', views.SaleLogisticsAssignView.as_view(), name='assign_logistics'),
    path('notificar-cliente/<int:pk>/', views.SaleNotifyClientView.as_view(), name='notify_client'),
    # Per-stop confirm / cancel
    path('ver/<int:sale_pk>/stop/<int:stop_pk>/confirmar/', views.StopConfirmView.as_view(), name='stop_confirm'),
    path('ver/<int:sale_pk>/stop/<int:stop_pk>/cancelar/', views.StopCancelView.as_view(), name='stop_cancel'),
    # API
    path('api/tour-details/<int:tour_id>/', views.get_tour_details, name='api_tour_details'),
    path('api/check-availability/', views.check_availability, name='api_check_availability'),
]
