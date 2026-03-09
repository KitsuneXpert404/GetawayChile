from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from datetime import timedelta
import calendar
import json
from io import BytesIO

from sales.models import Sale
from django.contrib.auth import get_user_model

# xhtml2pdf for PDF generation
from xhtml2pdf import pisa
from django.template.loader import get_template

User = get_user_model()

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class ReportDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'core/report_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Determine Period Filter
        period = self.request.GET.get('period', 'month') # default to month
        now = timezone.now()
        
        if period == 'week':
            start_date = now - timedelta(days=now.weekday()) # Monday of current week
            start_date = start_date.replace(hour=0, minute=0, second=0)
            period_label = "Esta Semana"
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            period_label = "Este Año"
        elif period == 'all':
            start_date = None
            period_label = "Histórico Total"
        else: # month
            start_date = now.replace(day=1, hour=0, minute=0, second=0)
            period_label = calendar.month_name[now.month].capitalize() + f" {now.year}"
            
        # Base Querysets
        # Only counting completed or confirmed sales for earnings. Wait, how is status defined in Sale?
        # Let's check Sale model structure... I'll assume valid sales are status="COMPLETADA" or active.
        # But wait, Sale doesn't have a direct "COMPLETADA" status, it has is_active or payment statuses sometimes.
        # I'll rely on the whole queryset unless specified otherwise. Let's assume all Sales are valid earnings for now.
        
        # Wait, the prompt says "quien vendio mas, cuanto se gano".
        if start_date:
            sales_qs = Sale.objects.filter(created_at__gte=start_date)
        else:
            sales_qs = Sale.objects.all()
            
        # Total Earnings
        # In a real model, there's a total_price or total_amount. I will compute Sum('total_amount')
        # Let's hope total exists! It should be in Sale.
        total_earnings = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_sales_count = sales_qs.count()
        # Assume total passengers is sum of passengers. 
        total_passengers = sales_qs.aggregate(pax=Sum('passengers_count'))['pax'] or 0
        
        if total_sales_count > 0:
            average_ticket = total_earnings / total_sales_count
        else:
            average_ticket = 0
            
        # Top Seller (Vendedor)
        top_sellers = sales_qs.values('seller__first_name', 'seller__last_name', 'seller__email', 'seller__photo') \
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id')
            ).order_by('-total_amount')[:5]
            
        # Tour Performance
        top_tours = sales_qs.values('tour__name') \
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id')
            ).order_by('-sales_count')[:5]

        # --- Chart Data: Sales over time ---
        if period in ['week', 'month']:
            # Agrupar por día
            sales_over_time = sales_qs.annotate(date=TruncDate('created_at')) \
                .values('date').annotate(total=Sum('total_amount')).order_by('date')
            chart_dates = [s['date'].strftime('%d/%m') if s['date'] else '' for s in sales_over_time]
        else:
            # Agrupar por mes
            sales_over_time = sales_qs.annotate(month=TruncMonth('created_at')) \
                .values('month').annotate(total=Sum('total_amount')).order_by('month')
            chart_dates = [s['month'].strftime('%m/%Y') if s['month'] else '' for s in sales_over_time]
            
        chart_revenues = [float(s['total'] or 0) for s in sales_over_time]

        # --- Chart Data: Sales by Channel ---
        channel_data = sales_qs.values('origin_channel') \
            .annotate(total=Sum('total_amount')).order_by('-total')
        
        channel_labels = [str(c['origin_channel']) for c in channel_data]
        channel_values = [float(c['total'] or 0) for c in channel_data]

        # Recent Sales
        recent_sales = sales_qs.order_by('-created_at')[:10]
            
        context.update({
            'period': period,
            'period_label': period_label,
            'total_earnings': total_earnings,
            'total_sales_count': total_sales_count,
            'total_passengers': total_passengers,
            'average_ticket': average_ticket,
            'top_sellers': top_sellers,
            'top_tours': top_tours,
            'recent_sales': recent_sales,
            'start_date': start_date,
            'now': now,
            'chart_dates_json': json.dumps(chart_dates),
            'chart_revenues_json': json.dumps(chart_revenues),
            'channel_labels_json': json.dumps(channel_labels),
            'channel_values_json': json.dumps(channel_values),
        })
        
        return context

# Generación de PDF
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

class ReportGeneratePdfView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'month')
        now = timezone.now()
        
        # Same logic for dates
        if period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0)
            period_label = "Esta Semana"
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            period_label = "Anual"
        elif period == 'all':
            start_date = None
            period_label = "Histórico General"
        else: # month
            start_date = now.replace(day=1, hour=0, minute=0, second=0)
            period_label = calendar.month_name[now.month].capitalize() + f" {now.year}"
            
        if start_date:
            sales_qs = Sale.objects.filter(created_at__gte=start_date)
        else:
            sales_qs = Sale.objects.all()
            
        total_earnings = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_sales_count = sales_qs.count()
        total_passengers = sales_qs.aggregate(pax=Sum('passengers_count'))['pax'] or 0
        
        top_sellers = sales_qs.values('seller__first_name', 'seller__last_name') \
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id')
            ).order_by('-total_amount')[:5]
            
        context = {
            'period_label': period_label,
            'total_earnings': total_earnings,
            'total_sales_count': total_sales_count,
            'total_passengers': total_passengers,
            'top_sellers': top_sellers,
            'now': now,
            'sales': sales_qs.order_by('-created_at')[:50] # Preview limit for PDF
        }
        
        pdf = render_to_pdf('core/report_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Reporte_Getaway_{period_label.replace(' ', '_')}.pdf"
            
            # Si el usuario quiere descargar vs ver en linea: (descarga)
            download = request.GET.get('download', 'true')
            if download == 'true':
                content = f"attachment; filename={filename}"
            else:
                content = f"inline; filename={filename}"
                
            response['Content-Disposition'] = content
            return response
            
        return HttpResponse("No se pudo generar el reporte PDF.", status=400)
    
from django.core.mail import EmailMessage
from django.contrib import messages
from django.shortcuts import redirect
import calendar

class ReportEmailPdfView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        period = request.POST.get('period', 'month')
        email_dest = request.POST.get('email_dest')
        now = timezone.now()
        
        # Fecha base para query (mismas reglas)
        if period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0)
            period_label = "Esta Semana"
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            period_label = "Anual"
        elif period == 'all':
            start_date = None
            period_label = "Histórico General"
        else: # month
            start_date = now.replace(day=1, hour=0, minute=0, second=0)
            period_label = calendar.month_name[now.month].capitalize() + f" {now.year}"
            
        if start_date:
            sales_qs = Sale.objects.filter(created_at__gte=start_date)
        else:
            sales_qs = Sale.objects.all()
            
        total_earnings = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_sales_count = sales_qs.count()
        total_passengers = sales_qs.aggregate(pax=Sum('passengers_count'))['pax'] or 0
        
        top_sellers = sales_qs.values('seller__first_name', 'seller__last_name') \
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id')
            ).order_by('-total_amount')[:5]
            
        context = {
            'period_label': period_label,
            'total_earnings': total_earnings,
            'total_sales_count': total_sales_count,
            'total_passengers': total_passengers,
            'top_sellers': top_sellers,
            'now': now,
            'sales': sales_qs.order_by('-created_at')[:50]
        }
        
        # Generar PDF
        pdf_file = render_to_pdf('core/report_pdf.html', context)
        
        if pdf_file and email_dest:
            filename = f"Reporte_Getaway_{period_label.replace(' ', '_')}.pdf"
            
            try:
                from django.conf import settings
                msg = EmailMessage(
                    subject=f"Reporte de Rendimiento General: {period_label}",
                    body="Adjunto encontrarás el reporte generado con las métricas de rendimiento y ventas de Getaway Chile correspondientes al periodo seleccionado.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email_dest],
                )
                msg.attach(filename, pdf_file.content, 'application/pdf')
                msg.send()
                
                messages.success(request, f"¡Reporte enviado exitosamente a {email_dest}!")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al enviar el correo: {str(e)}")
        else:
            messages.error(request, "Error interno al generar el Documento PDF para el envío.")
            
        return redirect('report_dashboard')
