from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.mixins import AdminOrLogisticsRequiredMixin, LogisticsRequiredMixin
from .models import DailyOperation, Vehicle
from catalog.models import Tour, TourAvailability
from sales.models import Sale
import datetime

class LogisticsQuotasManagerView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'logistics/quotas_manager.html'

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'LOGISTICA', 'VENDEDOR']

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        from sales.models import SaleTour
        context = super().get_context_data(**kwargs)

        # ── Date for the "ajuste" section ──────────────────────────
        selected_date_str = self.request.GET.get('date')
        if not selected_date_str:
            selected_date = datetime.date.today()
            selected_date_str = selected_date.isoformat()
        else:
            try:
                selected_date = datetime.date.fromisoformat(selected_date_str)
            except ValueError:
                selected_date = datetime.date.today()
                selected_date_str = selected_date.isoformat()

        prev_date = (selected_date - datetime.timedelta(days=1)).isoformat()
        next_date = (selected_date + datetime.timedelta(days=1)).isoformat()

        # ── All active regular tours ────────────────────────────────
        tours = Tour.objects.filter(active=True, tour_type='REGULAR').order_by('name')

        # ── GLOBAL overview: one row per tour (base cupo + next-30d reservations) ──
        today = datetime.date.today()
        next_30 = today + datetime.timedelta(days=30)
        DAY_LETTERS = ['D', 'L', 'M', 'X', 'J', 'V', 'S']  # 0=Dom … 6=Sab

        all_tours_data = []
        for tour in tours:
            # Sum of reserved pax across all future dates (next 30 days)
            reserved_total = SaleTour.objects.filter(
                tour=tour,
                tour_date__gte=today,
                tour_date__lte=next_30,
            ).exclude(sale__status='CANCELADA').aggregate(
                total=Sum('sale__passengers_count')
            )['total'] or 0

            # Count overrides for this tour in next 30 days
            overrides = TourAvailability.objects.filter(
                tour=tour,
                fecha__gte=today,
                fecha__lte=next_30,
            ).count()

            # Parse operative days and build display list
            try:
                active_days = {int(x.strip()) for x in tour.dias_operativos.split(',') if x.strip()}
            except ValueError:
                active_days = set()
            days_display = [{'letter': DAY_LETTERS[i], 'active': i in active_days} for i in range(7)]

            all_tours_data.append({
                'tour': tour,
                'cupo_base': tour.cupo_maximo_diario,
                'days_display': days_display,
                'reservados_30d': reserved_total,
                'overrides_30d': overrides,
            })

        # ── DATE-SPECIFIC data (for the ajuste section below) ───────
        weekday = selected_date.isoweekday() % 7
        tours_data = []
        for tour in tours:
            dias_operativos = [int(x.strip()) for x in tour.dias_operativos.split(',') if x.strip()]
            if weekday not in dias_operativos:
                continue
            try:
                avail, _ = TourAvailability.objects.get_or_create(
                    tour=tour,
                    fecha=selected_date,
                    defaults={'cupo_maximo': tour.cupo_maximo_diario}
                )
                cupo_disponible = avail.cupo_disponible
                cupo_maximo = avail.cupo_maximo
                cupo_reservado = avail.cupo_reservado_actual
            except Exception:
                reserved = SaleTour.objects.filter(
                    tour=tour, tour_date=selected_date
                ).exclude(sale__status='CANCELADA').aggregate(
                    total_pax=Sum('sale__passengers_count')
                )['total_pax'] or 0
                cupo_disponible = max(0, tour.cupo_maximo_diario - reserved)
                cupo_maximo = tour.cupo_maximo_diario
                cupo_reservado = reserved

            tours_data.append({
                'tour': tour,
                'cupo_maximo': cupo_maximo,
                'cupo_reservado': cupo_reservado,
                'cupo_disponible': cupo_disponible,
                'is_override': cupo_maximo != tour.cupo_maximo_diario,
            })

        from core.context_processors import get_role_template
        role_template = get_role_template(self.request.user)
        context.update({
            'role_base_template': role_template,
            'selected_date': selected_date_str,
            'selected_date_obj': selected_date,
            'prev_date': prev_date,
            'next_date': next_date,
            'all_tours_data': all_tours_data,
            'tours_data': tours_data,
            'today': today,
        })
        return context

class LogisticsHomeView(LoginRequiredMixin, LogisticsRequiredMixin, TemplateView):
    template_name = 'logistics/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from sales.models import Sale, SaleTour
        import datetime

        today = datetime.date.today()
        all_active = Sale.objects.exclude(status='CANCELADA')

        # KPIs Globales
        context['count_pending'] = all_active.filter(status='PENDIENTE').count()
        context['count_confirmed'] = all_active.filter(status='CONFIRMADA').count()
        context['count_without_vehicle'] = SaleTour.objects.filter(
            sale__status='CONFIRMADA', assigned_vehicle__isnull=True
        ).exclude(sale__status='CANCELADA').values('sale_id').distinct().count()
        context['count_not_notified'] = all_active.filter(status='CONFIRMADA', client_notified=False).count()

        # Próximos 3 días de actividad sumatoria
        next_days = [today + datetime.timedelta(days=i) for i in range(3)]
        pax_por_dia = []
        for d in next_days:
            from django.db.models import Sum
            res = SaleTour.objects.filter(
                tour_date=d
            ).exclude(sale__status='CANCELADA').aggregate(
                total=Sum('sale__passengers_count')
            )['total'] or 0
            pax_por_dia.append({'date': d, 'pax': res})
        
        context['pax_por_dia'] = pax_por_dia
        context['today_str'] = today.isoformat()
        return context

class LogisticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'logistics/dashboard.html'

    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from sales.models import SaleTour
        from django.db.models import Q
        import collections
        from django.utils.dateformat import format as date_format

        # ── Date / navigation ─────────────────────────────────────────
        selected_date_str = self.request.GET.get('date', '')
        if not selected_date_str:
            selected_date = datetime.date.today()
            selected_date_str = selected_date.isoformat()
        else:
            try:
                selected_date = datetime.date.fromisoformat(selected_date_str)
            except ValueError:
                selected_date = datetime.date.today()
                selected_date_str = selected_date.isoformat()

        monday = selected_date - datetime.timedelta(days=selected_date.weekday())
        week_end = monday + datetime.timedelta(days=6)
        prev_date = (monday - datetime.timedelta(days=7)).isoformat()
        next_date = (monday + datetime.timedelta(days=7)).isoformat()

        context['selected_date'] = selected_date_str
        context['selected_date_obj'] = selected_date
        context['prev_date'] = prev_date
        context['next_date'] = next_date
        context['week_start'] = monday
        context['week_end'] = week_end

        # ── Daily view: SaleTour stops grouped by date → tour name ─────
        days_to_iterate = [monday + datetime.timedelta(days=i) for i in range(7)]
        stops_qs = (
            SaleTour.objects
            .filter(tour_date__range=(monday, week_end))
            .exclude(sale__status='CANCELADA')
            .select_related('tour', 'sale', 'sale__seller', 'sale__assigned_vehicle')
            .prefetch_related('sale__passengers')
            .order_by('tour_date', 'tour__name', 'sale__pickup_time', 'sale__created_at')
        )

        grouped_sales = collections.OrderedDict()
        for d in days_to_iterate:
            formatted_title = date_format(d, r'l, d \d\e F \d\e Y').title()
            grouped_sales[d.isoformat()] = {
                'date_obj': d,
                'title_str': formatted_title,
                'is_selected': d == selected_date,
                'tours': collections.OrderedDict()
            }

        for stop in stops_qs:
            if not stop.tour_date:
                continue
            d_str = stop.tour_date.isoformat()
            if d_str not in grouped_sales:
                continue
            sale = stop.sale
            t_name = stop.tour.name if stop.tour else 'Tour No Asignado'
            if stop.is_private:
                t_name += ' (PRIVADO)'
            day_group = grouped_sales[d_str]['tours']
            if t_name not in day_group:
                tour_obj = stop.tour
                cupo_disponible = None
                if tour_obj and not stop.is_private:
                    try:
                        avail, _ = TourAvailability.objects.get_or_create(
                            tour=tour_obj, fecha=stop.tour_date,
                            defaults={'cupo_maximo': tour_obj.cupo_maximo_diario}
                        )
                        cupo_disponible = avail.cupo_disponible
                    except Exception:
                        pass
                day_group[t_name] = {'tour_obj': tour_obj, 'sales': [], 'total_pax': 0, 'cupo_disponible': cupo_disponible}
            stop.client_full_name = f'{sale.client_first_name} {sale.client_last_name}'.strip()
            stop.sale_obj = sale
            day_group[t_name]['sales'].append(stop)
            day_group[t_name]['total_pax'] += (stop.pax_adults + stop.pax_infants)

        context['grouped_sales'] = grouped_sales
        context['grouped_sales_count'] = len(grouped_sales)

        # ── Weekly summary ribbon — FIXED: uses SaleTour.tour_date (multi-stop safe) ─
        week_stops_qs = SaleTour.objects.filter(
            tour_date__range=(monday, week_end)
        ).exclude(sale__status='CANCELADA').select_related('sale')

        weekly_summary = []
        for i in range(7):
            d = monday + datetime.timedelta(days=i)
            day_stops = [s for s in week_stops_qs if s.tour_date == d]
            # Deduplicate sales for pax count (a sale may have multiple stops on same day)
            seen_sales = {}
            for s in day_stops:
                if s.sale_id not in seen_sales:
                    seen_sales[s.sale_id] = s.pax_adults + s.pax_infants
            total_pax = sum(seen_sales.values())
            weekly_summary.append({
                'date_obj': d,
                'date_str': d.isoformat(),
                'short_day': date_format(d, 'D'),
                'day_num': date_format(d, 'd'),
                'pax': total_pax,
                'sales_count': len(set(s.sale_id for s in day_stops)),
                'is_selected': d == selected_date,
                'is_today': d == datetime.date.today(),
            })
        context['weekly_summary'] = weekly_summary

        # ── KPIs ──────────────────────────────────────────────────────
        today = datetime.date.today()
        all_active = Sale.objects.exclude(status='CANCELADA')
        context['count_pending'] = all_active.filter(status='PENDIENTE').count()
        context['count_confirmed'] = all_active.filter(status='CONFIRMADA').count()
        # Without vehicle: any confirmed sale that has at least one stop without assigned_vehicle
        context['count_without_vehicle'] = SaleTour.objects.filter(
            sale__status='CONFIRMADA', assigned_vehicle__isnull=True
        ).exclude(sale__status='CANCELADA').values('sale_id').distinct().count()
        context['count_not_notified'] = all_active.filter(status='CONFIRMADA', client_notified=False).count()

        # ── Management table (Centro de Operaciones) with filters ──────
        date_filter = self.request.GET.get('fdate', '')
        status_filter = self.request.GET.get('status', '')
        search_q = self.request.GET.get('q', '').strip()

        mgmt_qs = Sale.objects.select_related(
            'seller', 'tour', 'assigned_vehicle', 'confirmed_by'
        ).prefetch_related('tour_stops__tour').order_by('-created_at')

        if date_filter:
            try:
                filter_date = datetime.date.fromisoformat(date_filter)
                mgmt_qs = mgmt_qs.filter(tour_stops__tour_date=filter_date).distinct()
            except ValueError:
                date_filter = ''
        if status_filter:
            mgmt_qs = mgmt_qs.filter(status=status_filter)
        if search_q:
            mgmt_qs = mgmt_qs.filter(
                Q(client_first_name__icontains=search_q) |
                Q(client_last_name__icontains=search_q) |
                Q(client_rut_passport__icontains=search_q) |
                Q(client_email__icontains=search_q) |
                Q(client_phone__icontains=search_q)
            )

        status_map = {
            'CONFIRMADA': ('gc-badge-green', 'fa-check-circle', 'Confirmada'),
            'PENDIENTE':  ('gc-badge-gold', 'fa-clock', 'Pendiente'),
            'CANCELADA':  ('gc-badge-red', 'fa-times-circle', 'Cancelada'),
        }
        pay_map = {
            'PAGADO':   ('gc-badge-green', 'Pagado'),
            'ABONADO':  ('gc-badge-gold', 'Abonado'),
            'PENDIENTE': ('gc-badge-red', 'Pendiente'),
        }
        sales_rows = []
        for sale in mgmt_qs:
            first_stop = sale.tour_stops.first()
            if first_stop:
                tour_display = ('Tour Privado — ' if first_stop.is_private else '') + (first_stop.tour.name[:30] if first_stop.tour else 'Sin tour')
                stops_summary = ', '.join(
                    f"{s.tour_date.strftime('%d/%m') if s.tour_date else '?'}"
                    for s in sale.tour_stops.all()
                )
                pax_display = f"{first_stop.pax_adults}A" + (f"+{first_stop.pax_infants}I" if first_stop.pax_infants else '')
            else:
                tour_display = '—'; stops_summary = '—'; pax_display = '—'
            s_class, s_icon, s_label = status_map.get(sale.status, ('gc-badge-red', 'fa-times-circle', sale.status))
            p_class, p_label = pay_map.get(sale.payment_status, ('gc-badge-red', sale.payment_status))
            sales_rows.append({
                'obj': sale,
                'tour_display': tour_display,
                'stops_summary': stops_summary,
                'pax_display': pax_display,
                'row_class': {'CONFIRMADA': 'ops-row-confirmed', 'PENDIENTE': 'ops-row-pending'}.get(sale.status, 'ops-row-cancelled'),
                'status_class': s_class, 'status_icon': s_icon, 'status_label': s_label,
                'pay_class': p_class, 'pay_label': p_label,
                'cur_sym': {'USD': 'US$', 'BRL': 'R$'}.get(sale.currency, '$'),
                'is_confirmed': sale.status == 'CONFIRMADA',
                'can_confirm': sale.status == 'PENDIENTE',
                'can_notify': sale.status == 'CONFIRMADA' and bool(sale.client_email),
                'client_full_name': f'{sale.client_first_name} {sale.client_last_name}',
                'client_email_short': (sale.client_email or '')[:22],
                'client_phone': sale.client_phone or '—',
                'detail_url': f'/dashboard/logistics/venta/{sale.pk}/',
                'manage_url': f'/dashboard/logistics/gestionar/{sale.pk}/',
                'confirm_url': reverse('sales:confirm', args=[sale.pk]),
                'cancel_url': reverse('sales:cancel', args=[sale.pk]),
                'notify_url': reverse('sales:notify_client', args=[sale.pk]),
                'assign_stop_first_url': (
                    f'/dashboard/logistics/asignar-stop/{sale.pk}/stop/{sale.tour_stops.first().pk}/'
                    if sale.tour_stops.exists() else '#'
                ),
            })

        context['sales_rows'] = sales_rows
        context['sales_count'] = len(sales_rows)
        context['date_filter'] = date_filter
        context['status_filter'] = status_filter
        context['search_q'] = search_q
        context['status_options'] = [
            {'value': '', 'label': '— Todos —', 'selected': not status_filter},
            {'value': 'PENDIENTE', 'label': 'Pendiente', 'selected': status_filter == 'PENDIENTE'},
            {'value': 'CONFIRMADA', 'label': 'Confirmada', 'selected': status_filter == 'CONFIRMADA'},
            {'value': 'CANCELADA', 'label': 'Cancelada', 'selected': status_filter == 'CANCELADA'},
        ]
        context['vehicles'] = Vehicle.objects.filter(is_active=True).order_by('owner_company', 'plate')
        context['today_str'] = today.isoformat()
        return context


from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.shortcuts import get_object_or_404
from .forms import DailyOperationForm, TourAvailabilityForm, VehicleForm, SaleLogisticsForm, StopLogisticsForm
from sales.models import Sale, SaleTour


# ----------------- VEHICLE CRUD -----------------

class VehicleListView(LoginRequiredMixin, LogisticsRequiredMixin, ListView):
    model = Vehicle
    template_name = 'logistics/vehicle_list.html'
    context_object_name = 'vehicles'
    ordering = ['owner_company', 'plate']

class VehicleCreateView(LoginRequiredMixin, LogisticsRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'logistics/vehicle_form.html'
    success_url = reverse_lazy('logistics_vehicle_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Vehículo registrado correctamente.")
        return super().form_valid(form)

class VehicleUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'logistics/vehicle_form.html'
    success_url = reverse_lazy('logistics_vehicle_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Vehículo actualizado correctamente.")
        return super().form_valid(form)

class VehicleDeleteView(LoginRequiredMixin, LogisticsRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'logistics/vehicle_confirm_delete.html'
    success_url = reverse_lazy('logistics_vehicle_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Vehículo eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


class VehicleDetailView(LoginRequiredMixin, LogisticsRequiredMixin, DetailView):
    """Read-only fleet card — shows all vehicle and driver contact info."""
    model = Vehicle
    template_name = 'logistics/vehicle_detail.html'
    context_object_name = 'vehicle'

# ----------------- LOGISTICS ASSIGNMENTS -------------

class SaleLogisticsUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleLogisticsForm
    template_name = 'logistics/sale_assign_form.html'
    
    def get_success_url(self):
        date_str = self.object.tour_date.isoformat() if self.object.tour_date else ''
        return reverse_lazy('logistics_dashboard') + f"?date={date_str}"
        
    def form_valid(self, form):
        messages.success(self.request, f"Se actualizaron los datos logísticos de la Venta #{self.object.id}.")
        return super().form_valid(form)


class StopLogisticsUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    """Assign vehicle + pickup_time + notes to a single SaleTour stop."""
    model = SaleTour
    form_class = StopLogisticsForm
    template_name = 'logistics/stop_assign_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            SaleTour,
            pk=self.kwargs['stop_pk'],
            sale_id=self.kwargs['sale_pk']
        )

    def form_valid(self, form):
        stop = form.save(commit=False)
        stop.vehicle_assigned_at = timezone.now()
        stop.vehicle_assigned_by = self.request.user
        
        # Auto-confirm stop if a vehicle is assigned
        if stop.assigned_vehicle:
            if stop.stop_status != 'CONFIRMADA':
                stop.stop_status = 'CONFIRMADA'
                stop.stop_confirmed_at = timezone.now()
                # Using the request user as the confirmer
                stop.stop_confirmed_by = getattr(self.request, 'user', None)

        stop.save()
        tour_label = stop.tour.name if stop.tour else 'Tour Privado'
        date_label = stop.tour_date.strftime('%d/%m/%Y') if stop.tour_date else ''

        # Build WhatsApp deep-link if vehicle has a driver phone
        wa_url = ''
        if stop.assigned_vehicle:
            phone = stop.assigned_vehicle.contact_phone
            if phone:
                import urllib.parse
                wa_msg = stop.assigned_vehicle.build_whatsapp_message(stop)
                wa_url = f"https://wa.me/{phone.replace('+','').replace(' ','')}?text={urllib.parse.quote(wa_msg)}"

        messages.success(
            self.request,
            f"✅ Logística asignada para '{tour_label} {date_label}'." +
            (" <a href='{}' target='_blank' class='ms-2 fw-bold text-success'>"
             "<i class='fab fa-whatsapp'></i> Notificar conductor</a>".format(wa_url)
             if wa_url else " (Este vehículo no tiene teléfono de conductor registrado)")
        )
        # Redirect to logistics manage view (not sales)
        return redirect('logistics_sale_manage', pk=self.kwargs['sale_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stop'] = self.get_object()
        ctx['sale'] = ctx['stop'].sale
        return ctx



class TripManagementView(LoginRequiredMixin, LogisticsRequiredMixin, TemplateView):
    """Logistics trip management: shows all sales with their per-stop logistics assignments."""
    template_name = 'logistics/trip_management.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from sales.models import Sale, SaleTour
        from django.db.models import Q

        date_str = self.request.GET.get('date', '')
        search_q = self.request.GET.get('q', '').strip()

        qs = Sale.objects.select_related(
            'seller', 'tour', 'assigned_vehicle', 'confirmed_by'
        ).prefetch_related(
            'tour_stops__tour',
            'tour_stops__assigned_vehicle',
            'tour_stops__vehicle_assigned_by',
        ).exclude(status='CANCELADA').order_by('-created_at')

        if date_str:
            try:
                filter_date = datetime.date.fromisoformat(date_str)
                qs = qs.filter(tour_stops__tour_date=filter_date)
            except ValueError:
                date_str = ''

        if search_q:
            qs = qs.filter(
                Q(client_first_name__icontains=search_q) |
                Q(client_last_name__icontains=search_q) |
                Q(client_rut_passport__icontains=search_q) |
                Q(client_phone__icontains=search_q)
            )

        qs = qs.distinct()
        ctx['sales'] = qs
        ctx['vehicles'] = Vehicle.objects.filter(is_active=True).order_by('owner_company')
        ctx['date_filter'] = date_str
        ctx['search_q'] = search_q
        ctx['today_str'] = datetime.date.today().isoformat()
        return ctx


from django.views.generic import DetailView

class LogisticsSaleDetailView(LoginRequiredMixin, LogisticsRequiredMixin, DetailView):
    """Read-only logistics detail of a sale — shows client info, stops, per-stop logistics. NO action buttons."""
    template_name = 'logistics/sale_detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        from sales.models import Sale
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
        ctx['back_url'] = reverse('logistics_sales_ops')
        ctx['view_only'] = True   # signals template to hide action buttons
        return ctx


class LogisticsSaleManageView(LoginRequiredMixin, LogisticsRequiredMixin, DetailView):
    """Full management view for logistics — confirm, cancel, assign vehicle, notify & traceability."""
    template_name = 'logistics/sale_manage.html'
    context_object_name = 'sale'

    def get_queryset(self):
        from sales.models import Sale
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
        sale = self.object
        ctx['back_url'] = reverse('logistics_sales_ops')
        ctx['view_only'] = False
        # URLs for actions
        ctx['confirm_url'] = reverse('sales:confirm', args=[sale.pk])
        ctx['cancel_url'] = reverse('sales:cancel', args=[sale.pk])
        ctx['notify_url'] = reverse('sales:notify_client', args=[sale.pk])
        # Available vehicles for assignment dropdowns
        ctx['vehicles'] = Vehicle.objects.filter(is_active=True).order_by('owner_company', 'plate')
        # Traceability: build event list from model timestamps
        events = []
        if sale.created_at:
            events.append({'icon': 'fa-plus-circle', 'color': '#6b7280', 'label': 'Venta registrada', 'dt': sale.created_at,
                           'by': f'{sale.seller.get_full_name()} ({sale.seller.get_role_display()})' if sale.seller else '—'})
        if sale.confirmed_at:
            events.append({'icon': 'fa-check-circle', 'color': '#059669', 'label': 'Venta confirmada', 'dt': sale.confirmed_at,
                           'by': sale.confirmed_by.get_full_name() if sale.confirmed_by else '—'})
        for stop in sale.tour_stops.all():
            if stop.vehicle_assigned_at:
                events.append({'icon': 'fa-truck', 'color': '#2563eb', 'label': f'Vehículo asignado — {stop.tour.name if stop.tour else "Stop"}',
                                'dt': stop.vehicle_assigned_at,
                                'by': stop.vehicle_assigned_by.get_full_name() if stop.vehicle_assigned_by else '—'})
                                
            # Get DailyOperation for this stop to inject Field Operation Check-in/out
            if stop.assigned_vehicle and stop.tour and stop.tour_date:
                ops = DailyOperation.objects.filter(
                    tour=stop.tour, date=stop.tour_date, vehicle=stop.assigned_vehicle
                )
                for op in ops:
                    if op.check_in_at:
                        events.append({
                            'icon': 'fa-play-circle', 
                            'color': '#10b981', 
                            'label': f'Viaje Iniciado (Check-in) — {stop.tour.name}',
                            'dt': op.check_in_at,
                            'by': op.check_in_by.get_full_name() if op.check_in_by else 'Guía/Conductor'
                        })
                    if op.check_out_at:
                        events.append({
                            'icon': 'fa-flag-checkered', 
                            'color': '#6b7280', 
                            'label': f'Viaje Terminado (Check-out) — {stop.tour.name}',
                            'dt': op.check_out_at,
                            'by': op.check_out_by.get_full_name() if op.check_out_by else 'Guía/Conductor'
                        })

        if sale.client_notified and sale.client_notified_at:
            events.append({'icon': 'fa-paper-plane', 'color': '#B5823C', 'label': 'Cliente notificado', 'dt': sale.client_notified_at, 'by': '—'})
        if sale.cancelled_at if hasattr(sale, 'cancelled_at') else False:
            events.append({'icon': 'fa-times-circle', 'color': '#dc2626', 'label': 'Venta cancelada', 'dt': sale.cancelled_at, 'by': '—'})
        events.sort(key=lambda e: e['dt'])
        ctx['trace_events'] = events
        return ctx


# ----------------- LOGISTICS / QUOTAS VIEWS -----------------

class DailyOperationUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    model = DailyOperation
    form_class = DailyOperationForm
    template_name = 'logistics/operation_form.html'
    
    def get_object(self, queryset=None):
        # Determine Tour and Date from URL
        tour_id = self.kwargs.get('tour_id')
        date_str = self.kwargs.get('date')
        date_obj = datetime.date.fromisoformat(date_str)
        
        # Get or Create
        obj, created = DailyOperation.objects.get_or_create(
            tour_id=tour_id,
            date=date_obj,
            defaults={'status': 'PENDIENTE'}
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tour'] = Tour.objects.get(pk=self.kwargs.get('tour_id'))
        context['date'] = self.kwargs.get('date')
        return context

    def get_success_url(self):
        return reverse_lazy('logistics_dashboard') + f"?date={self.kwargs.get('date')}&view=logistics"


class TourBaseQuotaUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    """Updates the master cupo_maximo_diario for a Tour (affects all future days without overrides)."""
    model = Tour
    fields = ['cupo_maximo_diario']
    template_name = 'logistics/tour_base_quota_form.html'
    pk_url_kwarg = 'tour_id'

    def get_success_url(self):
        messages.success(self.request, f"Cupo base actualizado a {self.object.cupo_maximo_diario} para el tour '{self.object.name}'.")
        return reverse_lazy('logistics_quotas_manager')


class TourAvailabilityUpdateView(LoginRequiredMixin, LogisticsRequiredMixin, UpdateView):
    model = TourAvailability
    form_class = TourAvailabilityForm
    template_name = 'logistics/availability_form.html'
    
    def get_object(self, queryset=None):
        tour_id = self.kwargs.get('tour_id')
        date_str = self.kwargs.get('date')
        date_obj = datetime.date.fromisoformat(date_str)
        
        # Get Tour to check default quota
        tour = Tour.objects.get(pk=tour_id)
        
        obj, created = TourAvailability.objects.get_or_create(
            tour_id=tour_id,
            fecha=date_obj,
            defaults={'cupo_maximo': tour.cupo_maximo_diario}
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tour'] = Tour.objects.get(pk=self.kwargs.get('tour_id'))
        context['date'] = self.kwargs.get('date')
        return context

    def get_success_url(self):
        return reverse_lazy('logistics_quotas_manager') + f"?date={self.kwargs.get('date')}"


class TourReservationsDetailView(LoginRequiredMixin, LogisticsRequiredMixin, ListView):
    model = Sale
    template_name = 'logistics/reservations_list.html'
    context_object_name = 'sales'
    
    def get_queryset(self):
        tour_id = self.kwargs.get('tour_id')
        date_str = self.kwargs.get('date')
        return Sale.objects.filter(tour_id=tour_id, tour_date=date_str).exclude(payment_status='RECHAZADA')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tour'] = Tour.objects.get(pk=self.kwargs.get('tour_id'))
        context['date'] = self.kwargs.get('date')
        return context


# ============================================================
# SALES OPERATIONS DASHBOARD — fusionado en LogisticsDashboardView
# ============================================================
# El Centro de Operaciones fue fusionado con el Diario de Operaciones.
# Esta vista redirige al dashboard unificado para mantener compatibilidad con URLs existentes.
class SalesOperationsDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA'])

    def get(self, request, *args, **kwargs):
        return redirect('/dashboard/logistics/dashboard/')

# ============================================================
# FIELD OPERATIONS DASHBOARD (CONDUCTORS AND GUIDES)
# ============================================================
class FieldOperationsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'logistics/field_operations.html'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in ['CONDUCTOR', 'GUIA', 'ADMIN', 'LOGISTICA']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Q
        
        selected_date_str = self.request.GET.get('date', '')
        if not selected_date_str:
            selected_date = datetime.date.today()
            selected_date_str = selected_date.isoformat()
        else:
            try:
                selected_date = datetime.date.fromisoformat(selected_date_str)
            except ValueError:
                selected_date = datetime.date.today()
                selected_date_str = selected_date.isoformat()
                
        prev_date = (selected_date - datetime.timedelta(days=1)).isoformat()
        next_date = (selected_date + datetime.timedelta(days=1)).isoformat()

        # Build query for the current user's assigned operations
        qs = DailyOperation.objects.filter(date=selected_date).select_related('tour', 'vehicle', 'driver', 'guide')
        if not getattr(self.request.user, 'is_admin', False) and self.request.user.role not in ['ADMIN', 'LOGISTICA']:
            qs = qs.filter(Q(driver=self.request.user) | Q(guide=self.request.user))
            
        operations = list(qs)
        
        # For each operation, attach the sales and passengers
        for op in operations:
            op.sales_list = SaleTour.objects.filter(
                tour=op.tour, 
                tour_date=op.date,
                assigned_vehicle=op.vehicle
            ).exclude(sale__status='CANCELADA').select_related('sale').prefetch_related('sale__passengers').order_by('pickup_time')
            
            pax_count = 0
            for st in op.sales_list:
                pax_count += (st.pax_adults + st.pax_infants)
            
            op.total_passengers = pax_count

        context['selected_date'] = selected_date_str
        context['selected_date_obj'] = selected_date
        context['prev_date'] = prev_date
        context['next_date'] = next_date
        context['operations'] = operations
        
        return context

class FieldOperationCheckInView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in ['CONDUCTOR', 'GUIA', 'ADMIN', 'LOGISTICA']
        
    def post(self, request, pk):
        op = get_object_or_404(DailyOperation, pk=pk)
        
        if not op.check_in_at:
            from django.utils import timezone
            op.check_in_at = timezone.now()
            op.check_in_by = request.user
            op.save(update_fields=['check_in_at', 'check_in_by'])
            messages.success(request, f"¡Check-in realizado con éxito para el viaje del {op.tour.name}!")
        else:
            messages.warning(request, "Este viaje ya tenía un Check-in registrado previamente.")
            
        return redirect(request.META.get('HTTP_REFERER', 'field_operations_dashboard'))

class FieldOperationCheckOutView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in ['CONDUCTOR', 'GUIA', 'ADMIN', 'LOGISTICA']
        
    def post(self, request, pk):
        op = get_object_or_404(DailyOperation, pk=pk)
        
        if not op.check_out_at:
            from django.utils import timezone
            op.check_out_at = timezone.now()
            op.check_out_by = request.user
            op.save(update_fields=['check_out_at', 'check_out_by'])
            messages.success(request, f"Check-out (Fin de viaje) registrado para {op.tour.name}.")
        else:
            messages.warning(request, "Este viaje ya tenía un Check-out registrado previamente.")
            
        return redirect(request.META.get('HTTP_REFERER', 'field_operations_dashboard'))

class VehicleOccupancyDashboardView(LoginRequiredMixin, LogisticsRequiredMixin, TemplateView):
    """
    Dashboard to visualize the occupancy generic seat map of all active operations for a given date.
    """
    template_name = 'logistics/vehicle_occupancy.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Sum
        from sales.models import SaleTour
        import datetime

        date_str = self.request.GET.get('date', '')
        if not date_str:
            target_date = datetime.date.today()
            date_str = target_date.isoformat()
        else:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                target_date = datetime.date.today()
                date_str = target_date.isoformat()

        # Fetch distinct vehicle+tour combinations from assigned SaleTours
        assigned_stops = SaleTour.objects.filter(
            tour_date=target_date,
            assigned_vehicle__isnull=False,
            stop_status='CONFIRMADA'
        ).exclude(sale__status='CANCELADA').select_related(
            'tour', 'assigned_vehicle', 'sale'
        )

        # Group the stops by vehicle and tour
        from collections import defaultdict
        groups = defaultdict(list)
        for stop in assigned_stops:
            groups[(stop.assigned_vehicle_id, stop.tour_id)].append(stop)

        ops_data = []
        for (vid, tid), stops in groups.items():
            vehicle = stops[0].assigned_vehicle
            tour = stops[0].tour
            
            pax = sum((s.pax_adults or 0) + (s.pax_infants or 0) for s in stops)
            cap = vehicle.capacity if vehicle else 0
            
            # Find if there is a DailyOperation to get the driver (optional at this stage)
            op = DailyOperation.objects.filter(date=target_date, vehicle=vehicle, tour=tour).first()
            driver = op.driver if op and op.driver else vehicle.default_driver
            
            passengers_list = []
            for stop in stops:
                pax_count = (stop.pax_adults or 0) + (stop.pax_infants or 0)
                pickup = stop.pickup_time or stop.sale.pickup_time
                passengers_list.append({
                    'sale_id': stop.sale.id,
                    'client_name': f"{stop.sale.client_first_name} {stop.sale.client_last_name}".strip(),
                    'pax_count': pax_count,
                    'hotel': stop.sale.hotel_address,
                    'pickup_time': pickup,
                    'phone': stop.sale.client_phone,
                    'notes': stop.logistics_notes
                })
                
            # Sort passengers list by pickup time
            passengers_list.sort(key=lambda x: x['pickup_time'] or datetime.time(23, 59))
            
            # Build generic seat array: length = capacity, True = occupied, False = empty
            seats = []
            for i in range(cap):
                if i < pax:
                    seats.append({'id': i+1, 'occupied': True})
                else:
                    seats.append({'id': i+1, 'occupied': False})
                    
            ops_data.append({
                'vehicle': vehicle,
                'tour': tour,
                'driver': driver,
                'capacity': cap,
                'pax': pax,
                'seats': seats,
                'passengers_list': passengers_list,
                'available': max(0, cap - pax),
                'percentage': min(100, int((pax / cap) * 100)) if cap > 0 else 0
            })

        ctx['date_str'] = date_str
        ctx['date_obj'] = target_date
        ctx['prev_date'] = (target_date - datetime.timedelta(days=1)).isoformat()
        ctx['next_date'] = (target_date + datetime.timedelta(days=1)).isoformat()
        ctx['ops_data'] = ops_data
        return ctx

