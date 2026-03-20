from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from users import views_admin
from . import views_history
from . import views_reports
from . import views_public

urlpatterns = [
    # ── PUBLIC (Client Website) ──────────────────────────────────────
    path('', views_public.PublicHomeView.as_view(), name='public_home'),
    path('tours/', views_public.PublicToursView.as_view(), name='public_tours'),
    path('tour/<int:pk>/', views_public.PublicTourDetailView.as_view(), name='public_tour_detail'),
    path('tours-privados/', views_public.PublicToursPrivadosView.as_view(), name='public_tours_privados'),
    path('transporte/', views_public.PublicTransporteView.as_view(), name='public_transporte'),
    path('quienes-somos/', views_public.PublicQuienesSomosView.as_view(), name='public_quienes_somos'),
    path('contacto/', views_public.PublicContactoView.as_view(), name='public_contacto'),
    path('reservar/', views_public.PublicReservarView.as_view(), name='public_reservar'),

    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        html_email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/password-reset/complete/'
    ), name='password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # User Management
    path('dashboard/users/', views_admin.UserListView.as_view(), name='user_list'),
    path('dashboard/users/create/', views_admin.UserCreateView.as_view(), name='user_create'),
    path('dashboard/users/<int:pk>/edit/', views_admin.UserUpdateView.as_view(), name='user_update'),
    path('dashboard/users/<int:pk>/delete/', views_admin.UserDeleteView.as_view(), name='user_delete'),
    
    # User Profile / Password
    path('dashboard/profile/', views_admin.UserProfileView.as_view(), name='user_profile'),
    path('dashboard/password-change/', views_admin.UserChangePasswordView.as_view(), name='password_change'),

    # Reports
    path('dashboard/reports/', views_reports.ReportDashboardView.as_view(), name='report_dashboard'),
    path('dashboard/reports/pdf/', views_reports.ReportGeneratePdfView.as_view(), name='report_generate_pdf'),
    path('dashboard/reports/email-pdf/', views_reports.ReportEmailPdfView.as_view(), name='report_email_pdf'),
    path('dashboard/reports/ventas-excel/', views.export_sales_excel, name='export_sales_excel'),

    # Audit History
    path('dashboard/history/sales/', views_history.SaleHistoryListView.as_view(), name='history_sale_list'),
    path('dashboard/history/sales/seller/<int:user_id>/', views_history.SaleHistoryBySellerListView.as_view(), name='history_sale_by_seller'),
    path('dashboard/history/sales/<int:pk>/', views_history.AuditSaleDetailView.as_view(), name='audit_sale_detail'),
    path('dashboard/history/sales/<int:history_id>/restore/', views_history.SaleVersionRestoreView.as_view(), name='history_sale_restore'),
    path('dashboard/history/tours/', views_history.TourHistoryListView.as_view(), name='history_tour_list'),
    path('dashboard/history/tours/<int:history_id>/restore/', views_history.TourVersionRestoreView.as_view(), name='history_tour_restore'),
    path('dashboard/history/tours/<int:history_id>/pdf/', views_history.TourVersionPDFReportView.as_view(), name='history_tour_pdf'),
]
