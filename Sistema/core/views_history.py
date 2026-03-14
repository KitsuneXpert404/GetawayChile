import io
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa

from sales.models import Sale, SaleTour
from catalog.models import Tour
from core.mixins import AdminOrLogisticsRequiredMixin

class SaleHistoryListView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, ListView):
    template_name = 'core/history_sale_list.html'
    context_object_name = 'seller_groups'
    
    def get_queryset(self):
        qs = Sale.history.all().select_related('history_user').order_by('-history_date')
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(client_first_name__icontains=q) |
                Q(client_last_name__icontains=q) |
                Q(client_rut_passport__icontains=q) |
                Q(history_user__email__icontains=q) |
                Q(history_user__first_name__icontains=q)
            )
            
        grouped = {}
        for record in qs:
            user = record.history_user
            user_id = user.id if user else 0
            
            if user_id not in grouped:
                grouped[user_id] = {
                    'seller_id': user_id,
                    'seller_name': f"{user.first_name} {user.last_name}".strip() if user else "Sistema",
                    'seller_email': user.email if user else "Automático / Sin Asignar",
                    'total_actions': 0,
                    'records': []
                }
            
            grouped[user_id]['total_actions'] += 1
            if len(grouped[user_id]['records']) < 3:
                grouped[user_id]['records'].append(record)
                
        results = list(grouped.values())
        if results:
            results.sort(key=lambda x: x['records'][0].history_date if x['records'] else timezone.now(), reverse=True)
            
        return results

class SaleHistoryBySellerListView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, ListView):
    template_name = 'core/history_sale_by_seller.html'
    context_object_name = 'sale_groups'
    paginate_by = 30
    
    def get_queryset(self):
        seller_id = self.kwargs.get('user_id')
        if seller_id == 0:
            qs = Sale.history.filter(history_user__isnull=True)
        else:
            qs = Sale.history.filter(history_user_id=seller_id)
            
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(client_first_name__icontains=q) |
                Q(client_last_name__icontains=q) |
                Q(client_rut_passport__icontains=q) |
                Q(id__icontains=q)
            )
        qs = qs.order_by('-history_date')
        
        grouped = {}
        for record in qs:
            sid = record.id
            if sid not in grouped:
                grouped[sid] = {
                    'sale_id': sid,
                    'client_name': f"{record.client_first_name} {record.client_last_name}",
                    'client_rut': record.client_rut_passport,
                    'is_deleted': True,
                    'records': []
                }
            grouped[sid]['records'].append(record)
            
        existing_ids = set(Sale.objects.filter(id__in=grouped.keys()).values_list('id', flat=True))
        for sid in grouped:
            if sid in existing_ids:
                grouped[sid]['is_deleted'] = False
                
        results = list(grouped.values())
        if results:
            results.sort(key=lambda x: max([r.history_date for r in x['records']]), reverse=True)
            
        now = timezone.now()
        for group in results:
            recs = group['records']
            for i in range(len(recs)):
                rec = recs[i]
                start_date = rec.history_date
                if i == 0:
                    end_date = now if not group['is_deleted'] else rec.history_date
                else:
                    end_date = recs[i-1].history_date
                
                rec.valid_from = start_date
                rec.valid_to = end_date
                rec.is_current_active = (i == 0 and not group['is_deleted'])
                
        return results
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seller_id = self.kwargs.get('user_id')
        
        if seller_id == 0:
            context['seller_name'] = "Sistema"
            context['seller_email'] = "Acciones automáticas"
        else:
            from users.models import CustomUser
            user = get_object_or_404(CustomUser, id=seller_id)
            context['seller_name'] = f"{user.first_name} {user.last_name}"
            context['seller_email'] = user.email
            context['seller_id'] = seller_id
            
        return context

class SaleVersionRestoreView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, View):
    def post(self, request, history_id):
        historic_record = get_object_or_404(Sale.history.model, history_id=history_id)
        if hasattr(historic_record, 'instance'):
            historic_record.instance.save()
            messages.success(request, f"Se ha restaurado la venta de {historic_record.client_first_name} a la versión del {historic_record.history_date.strftime('%d/%m/%Y %H:%M')}.")
        return redirect('history_sale_list')

class TourHistoryListView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, ListView):
    template_name = 'core/history_tour_list.html'
    context_object_name = 'tour_groups'
    
    def get_queryset(self):
        q = self.request.GET.get('q', '')
        qs = Tour.history.all().order_by('-history_date')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(destination__icontains=q) |
                Q(history_user__email__icontains=q)
            )
            
        grouped = {}
        for record in qs:
            tid = record.id
            if tid not in grouped:
                grouped[tid] = {
                    'tour_id': tid,
                    'tour_name': record.name,
                    'is_deleted': True,
                    'records': []
                }
            grouped[tid]['records'].append(record)
            
        existing_ids = set(Tour.objects.filter(id__in=grouped.keys()).values_list('id', flat=True))
        for tid in grouped:
            if tid in existing_ids:
                grouped[tid]['is_deleted'] = False
                
        results = list(grouped.values())
        if results:
            results.sort(key=lambda x: max([r.history_date for r in x['records']]), reverse=True)
        
        now = timezone.now()
        for group in results:
            recs = group['records']
            # recs is sorted newest to oldest. We want to compare each rec with the one immediately older than it.
            for i in range(len(recs)):
                rec = recs[i]
                start_date = rec.history_date
                if i == 0:
                    end_date = now if not group['is_deleted'] else rec.history_date
                else:
                    end_date = recs[i-1].history_date
                
                sales_count = SaleTour.objects.filter(
                    tour_id=rec.id, 
                    sale__created_at__gte=start_date, 
                    sale__created_at__lt=end_date
                ).values('sale').distinct().count()
                
                rec.valid_from = start_date
                rec.valid_to = end_date
                rec.sales_count = sales_count
                rec.is_current_active = (i == 0 and not group['is_deleted'])

                # Compute changes
                changes = []
                # The "older" record is at index i+1
                if i < len(recs) - 1:
                    prev_rec = recs[i+1]
                    
                    fields_to_check = [
                        ('name', 'Nombre'),
                        ('tour_type', 'Tipo de Tour'),
                        ('precio_clp', 'Precio Base (CLP)'),
                        ('precio_adulto_clp', 'Precio Adulto (CLP)'),
                        ('precio_infante_clp', 'Precio Infante (CLP)'),
                        ('precio_usd', 'Precio Base (USD)'),
                        ('precio_adulto_usd', 'Precio Adulto (USD)'),
                        ('precio_infante_usd', 'Precio Infante (USD)'),
                        ('precio_brl', 'Precio Base (BRL)'),
                        ('precio_adulto_brl', 'Precio Adulto (BRL)'),
                        ('precio_infante_brl', 'Precio Infante (BRL)'),
                        ('active', 'Estado Activo'),
                        ('destination', 'Destino'),
                        ('duration', 'Duración'),
                        ('cupo_maximo_diario', 'Cupo Máximo'),
                    ]
                    
                    for field_name, friendly_name in fields_to_check:
                        old_val = getattr(prev_rec, field_name)
                        new_val = getattr(rec, field_name)
                        if old_val != new_val:
                            # Format booleans nicely
                            if isinstance(old_val, bool): old_val = 'Sí' if old_val else 'No'
                            if isinstance(new_val, bool): new_val = 'Sí' if new_val else 'No'
                            
                            # Format decimals without .00 if possible to save space
                            if old_val is None: old_val = 'N/A'
                            if new_val is None: new_val = 'N/A'
                            
                            changes.append(f"{friendly_name}: {old_val} ➔ {new_val}")
                            
                rec.changes_summary = changes
                
        return results

class TourVersionRestoreView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, View):
    def post(self, request, history_id):
        historic_record = get_object_or_404(Tour.history.model, history_id=history_id)
        if hasattr(historic_record, 'instance'):
            historic_record.instance.save()
            messages.success(request, f"Se ha restaurado el tour '{historic_record.name}' a la versión del {historic_record.history_date.strftime('%d/%m/%Y %H:%M')}.")
        return redirect('history_tour_list')
        
class TourVersionPDFReportView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, View):
    def get(self, request, history_id):
        historic_record = get_object_or_404(Tour.history.model, history_id=history_id)
        newer_record = Tour.history.filter(id=historic_record.id, history_date__gt=historic_record.history_date).order_by('history_date').first()
        
        start_date = historic_record.history_date
        end_date = newer_record.history_date if newer_record else timezone.now()
        
        sales_tours = SaleTour.objects.filter(
            tour_id=historic_record.id,
            sale__created_at__gte=start_date,
            sale__created_at__lt=end_date
        ).select_related('sale').order_by('sale__created_at')
        
        context = {
            'historic_record': historic_record,
            'start_date': start_date,
            'end_date': end_date,
            'sales_tours': sales_tours,
        }
        
        template_path = 'core/pdf_tour_version_sales.html'
        template = get_template(template_path)
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Reporte_Ventas_{historic_record.name}_{start_date.strftime("%Y%m%d")}.pdf"'
        
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generando PDF', status=500)
        return response

from django.views.generic import DetailView

class AuditSaleDetailView(LoginRequiredMixin, DetailView):
    """Read-only audit detail of a sale. Visible to those with access to history. NO action buttons."""
    template_name = 'core/audit_sale_detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        return Sale.objects.select_related(
            'tour', 'seller', 'assigned_vehicle', 'confirmed_by'
        ).prefetch_related(
            'passengers',
            'tour_stops__tour',
            'tour_stops__assigned_vehicle',
            'tour_stops__vehicle_assigned_by',
            'tour_stops__stop_confirmed_by',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['view_only'] = True
        return ctx
