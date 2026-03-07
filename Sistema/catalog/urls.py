from django.urls import path
from . import views

urlpatterns = [
    path('tours/', views.TourListView.as_view(), name='tour_list'),
    path('tours/create/', views.TourCreateView.as_view(), name='tour_create'),
    path('tours/<int:pk>/', views.TourDetailView.as_view(), name='tour_detail'), # Detail view
    path('tours/<int:pk>/update/', views.TourUpdateView.as_view(), name='tour_update'),
    path('tours/<int:pk>/delete/', views.TourDeleteView.as_view(), name='tour_delete'),
]
