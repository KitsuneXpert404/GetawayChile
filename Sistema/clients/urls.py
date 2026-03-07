from django.urls import path
from .views import ClientList, ClientDetail
from .views_agency import AgencyListView, AgencyCreateView, AgencyUpdateView, AgencyDeleteView

urlpatterns = [
    path("clients/", ClientList.as_view(), name="client-list"),
    path("clients/<int:pk>/", ClientDetail.as_view(), name="client-detail"),
    
    # Agencies CRUD
    path("agencies/", AgencyListView.as_view(), name="agency-list"),
    path("agencies/new/", AgencyCreateView.as_view(), name="agency-create"),
    path("agencies/<int:pk>/edit/", AgencyUpdateView.as_view(), name="agency-update"),
    path("agencies/<int:pk>/delete/", AgencyDeleteView.as_view(), name="agency-delete"),
]
