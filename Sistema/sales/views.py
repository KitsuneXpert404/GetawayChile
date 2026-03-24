from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import Sale, Passenger, SaleStatus, SaleTour
from .forms import SaleForm, PassengerFormSet, PassengerUpdateFormSet
from catalog.models import TourAvailability, Tour


@login_required
def get_tour_details(request, tour_id):
    try:
        tour = Tour.objects.get(pk=tour_id)
        data = {
            'tour_type': tour.tour_type,
            'precio_clp': tour.precio_clp,
            'precio_usd': tour.precio_usd,
            'precio_brl': tour.precio_brl,
            'dias_operativos': tour.get_dias_list(),
        }
        return JsonResponse(data)
    except Tour.DoesNotExist:
        return JsonResponse({'error': 'Tour no encontrado'}, status=404)


@login_required
def check_availability(request):
    tour_id = request.GET.get('tour_id')
    date_str = request.GET.get('date')
    passengers = request.GET.get('passengers', 1)

    if not tour_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        passengers = int(passengers)
        tour = Tour.objects.get(pk=tour_id)
        if tour.tour_type == 'PRIVADO':
            return JsonResponse({'available': True, 'is_private': True})

        if not date_str:
            return JsonResponse({
                'available': tour.cupo_maximo_diario >= passengers,
                'cupo_disponible': tour.cupo_maximo_diario,
                'is_private': False,
                'no_date': True
            })

        import datetime
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

        # Validate operational days
        # isoweekday: Mon=1, Tue=2, ... Sun=7. Project uses 0=Dom, 1=Lun ...
        weekday = date.isoweekday() % 7
        dias_operativos = [int(x.strip()) for x in tour.dias_operativos.split(',') if x.strip()]
        if weekday not in dias_operativos:
            # Map index to days for nice error string
            days_map = {0:'Dom', 1:'Lun', 2:'Mar', 3:'Mié', 4:'Jue', 5:'Vie', 6:'Sáb'}
            dias_str = ", ".join([days_map.get(d, str(d)) for d in dias_operativos])
            return JsonResponse({'error': f'Este tour solo opera: {dias_str}'})

        availability, created = TourAvailability.objects.get_or_create(
            tour=tour,
            fecha=date,
            defaults={'cupo_maximo': tour.cupo_maximo_diario}
        )

        has_space = availability.cupo_disponible >= passengers

        return JsonResponse({
            'available': has_space,
            'cupo_disponible': availability.cupo_disponible,
            'is_private': False
        })
    except Tour.DoesNotExist:
        return JsonResponse({'error': 'Tour no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'

    def dispatch(self, request, *args, **kwargs):
        # Admin and Logística users manage sales from the operations center
        u = request.user
        if u.is_authenticated and (getattr(u, 'is_admin', False) or u.role in ('ADMIN', 'LOGISTICA')):
            return redirect(reverse_lazy('logistics_sales_ops'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            Sale.objects
            .select_related('tour', 'seller')
            .prefetch_related('tour_stops__tour')
            .all()
            .order_by('-created_at')
        )
        
        # Security: Vendedores only see their own sales
        if self.request.user.role == 'VENDEDOR':
            qs = qs.filter(seller=self.request.user)

        seller_id = self.request.GET.get('seller')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        
        if seller_id and self.request.user.role != 'VENDEDOR':
            qs = qs.filter(seller_id=seller_id)
        if month:
            qs = qs.filter(created_at__month=month)
        if year:
            qs = qs.filter(created_at__year=year)
        return qs

    def get_context_data(self, **kwargs):
        from users.models import CustomUser
        import datetime
        context = super().get_context_data(**kwargs)
        context['sellers'] = CustomUser.objects.filter(
            sales_made__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        try:
            sel_seller = int(self.request.GET.get('seller', ''))
        except (ValueError, TypeError):
            sel_seller = None
        try:
            sel_month = int(self.request.GET.get('month', ''))
        except (ValueError, TypeError):
            sel_month = None
        try:
            sel_year = int(self.request.GET.get('year', ''))
        except (ValueError, TypeError):
            sel_year = None

        context['selected_seller'] = sel_seller
        context['selected_month'] = sel_month
        context['selected_year'] = sel_year

        sellers_qs = CustomUser.objects.filter(
            sales_made__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        context['sellers_options'] = [
            {
                'id': s.id,
                'label': f"{s.first_name} {s.last_name}{' (' + s.rut + ')' if getattr(s, 'rut', None) else ''}",
                'selected': s.id == sel_seller,
            }
            for s in sellers_qs
        ]

        months = [
            (1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),(5,'Mayo'),(6,'Junio'),
            (7,'Julio'),(8,'Agosto'),(9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre')
        ]
        context['months_options'] = [
            {'num': num, 'nombre': nombre, 'selected': num == sel_month}
            for num, nombre in months
        ]

        current_year = datetime.date.today().year
        context['years_options'] = [
            {'year': y, 'selected': y == sel_year}
            for y in range(current_year, current_year - 5, -1)
        ]
        return context


class SaleDetailView(LoginRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        qs = Sale.objects.select_related('tour', 'seller', 'assigned_vehicle', 'confirmed_by').prefetch_related('passengers', 'tour_stops__tour')
        if self.request.user.role == 'VENDEDOR':
            qs = qs.filter(seller=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        import datetime as dt
        from logistics.models import Vehicle
        sale = self.get_object()
        vehicles_qs = Vehicle.objects.filter(is_active=True).order_by('owner_company', 'plate')
        ctx['vehicle_options'] = [
            {
                'pk': v.pk,
                'label': f"{v.plate} — {v.owner_company} ({v.capacity} pax)",
                'is_selected': sale.assigned_vehicle_id == v.pk,
            }
            for v in vehicles_qs
        ]
        # Days until the earliest stop's tour date (for cancel-restriction logic)
        first_stop = sale.tour_stops.order_by('tour_date').first()
        tour_date = first_stop.tour_date if first_stop else sale.tour_date
        if tour_date:
            ctx['days_to_tour'] = (tour_date - dt.date.today()).days
        else:
            ctx['days_to_tour'] = None
        return ctx


def _parse_tour_stops(post_data):
    """
    Parse the JSON-encoded tour stops from the hidden `tour_stops_json` field.
    Returns a list of dicts with keys:
      tour_id, tour_date, tour_language, is_private, private_description, pax_adults, pax_infants, price_adult, price_infant, subtotal
    """
    raw = post_data.get('tour_stops_json', '[]')
    try:
        stops = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        stops = []
    return stops


def _save_tour_stops(sale, stops, passengers_count):
    """Delete old SaleTour rows and create fresh ones from the stops list."""
    sale.tour_stops.all().delete()
    total = 0
    for i, stop in enumerate(stops):
        tour_obj = None
        tour_id = stop.get('tour_id')
        if tour_id:
            try:
                tour_obj = Tour.objects.get(pk=int(tour_id))
            except (Tour.DoesNotExist, ValueError):
                pass

        pax_adults = 1
        pax_infants = 0
        price_adult = 0
        price_infant = 0
        
        try:
            pax_adults = int(float(stop.get('pax_adults', 1)))
            pax_infants = int(float(stop.get('pax_infants', 0)))
            price_adult = int(float(stop.get('price_adult', 0)))
            price_infant = int(float(stop.get('price_infant', 0)))
        except (ValueError, TypeError):
            pass

        subtotal = (pax_adults * price_adult) + (pax_infants * price_infant)

        SaleTour.objects.create(
            sale=sale,
            tour=tour_obj,
            tour_date=stop.get('tour_date') or None,
            tour_language=stop.get('tour_language', 'ES'),
            is_private=bool(stop.get('is_private', False)),
            private_description=stop.get('private_description', ''),
            pax_adults=pax_adults,
            pax_infants=pax_infants,
            price_adult=price_adult,
            price_infant=price_infant,
            subtotal=subtotal,
            order=i,
        )
        total += subtotal

    # Update the sale total and sum of passengers
    sale.total_amount = max(total, int(float(sale.total_amount)))  # keep manual override if > computed
    sale.save(update_fields=['total_amount'])


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class SaleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    def get_success_url(self):
        u = self.request.user
        if getattr(u, 'is_admin', False) or u.role == 'ADMIN':
            return reverse_lazy('logistics_sales_ops')
        return reverse_lazy('sales:list')

    def test_func(self):
        u = self.request.user
        # LOGISTICA cannot create sales, everyone else (ADMIN, VENDEDOR, CONDUCTOR) can
        return u.is_authenticated and not (u.role == 'LOGISTICA' and not getattr(u, 'is_admin', False))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Lock total_amount so it cannot be manually entered by the user
        if 'total_amount' in form.fields:
            form.fields['total_amount'].widget.attrs['readonly'] = True
        return form

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['passengers'] = PassengerFormSet(self.request.POST)
            data['existing_stops'] = json.dumps(_parse_tour_stops(self.request.POST), cls=DjangoJSONEncoder)
        else:
            data['passengers'] = PassengerFormSet()
            data['existing_stops'] = []
        # Pass tour data as pre-serialised JSON — avoids Django tags inside <script>
        from catalog.models import Tour as TourModel
        tours = TourModel.objects.filter(active=True).values(
            'id', 'name', 'precio_clp', 'precio_adulto_clp', 'precio_infante_clp',
            'precio_usd', 'precio_adulto_usd', 'precio_infante_usd',
            'precio_brl', 'precio_adulto_brl', 'precio_infante_brl'
        )
        data['tour_choices_json'] = json.dumps([
            {
                'id': str(t['id']),
                'name': t['name'],
                'precio_clp': float(t['precio_clp'] or 0),
                'precio_adulto_clp': float(t['precio_adulto_clp'] or 0),
                'precio_infante_clp': float(t['precio_infante_clp'] or 0),
                'precio_usd': float(t['precio_usd'] or 0),
                'precio_adulto_usd': float(t['precio_adulto_usd'] or 0),
                'precio_infante_usd': float(t['precio_infante_usd'] or 0),
                'precio_brl': float(t['precio_brl'] or 0),
                'precio_adulto_brl': float(t['precio_adulto_brl'] or 0),
                'precio_infante_brl': float(t['precio_infante_brl'] or 0),
            }
            for t in tours
        ])
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        passengers = context['passengers']

        # ── Validar formsets y stops antes de abrir la transacción ──
        if not passengers.is_valid():
            return self.render_to_response(self.get_context_data(form=form, passengers=passengers))

        stops = _parse_tour_stops(self.request.POST)

        if not stops:
            form.add_error(None, "Debes agregar al menos un Tour al itinerario antes de guardar la venta.")
            return self.form_invalid(form)

        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        for stop in stops:
            td = stop.get('tour_date')
            if td:
                try:
                    stop_date = datetime.datetime.strptime(td, '%Y-%m-%d').date()
                    if stop_date < today:
                        form.add_error(None, f"No puedes registrar ventas para días en el pasado ({td}).")
                        return self.form_invalid(form)
                except ValueError:
                    pass

        self.object = form.save(commit=False)
        self.object.seller = self.request.user

        # Use first stop's data as the "primary" tour on the Sale record
        if stops:
            first = stops[0]
            if first.get('tour_id'):
                try:
                    self.object.tour_id = int(first['tour_id'])
                except (ValueError, TypeError):
                    pass
            self.object.tour_date = first.get('tour_date') or None
            self.object.tour_language = first.get('tour_language', 'ES')
            self.object.is_private = bool(first.get('is_private', False))

        # Determine passenger count from POST (set by passenger list JS)
        try:
            pax = int(self.request.POST.get('passengers_count', 1))
        except (ValueError, TypeError):
            pax = 1
        self.object.passengers_count = pax

        tour = self.object.tour
        date = self.object.tour_date
        required_seats = self.object.passengers_count

        with transaction.atomic():
            if self.object.is_private or not tour:
                self.object.status = SaleStatus.PENDING_APPROVAL
                self.object.save()
                
                passengers.instance = self.object
                passengers.save()
                
                _save_tour_stops(self.object, stops, pax)
                messages.success(self.request, "Venta ingresada correctamente. Pendiente de confirmación logística.")
                return redirect(self.get_success_url())

            # Regular tour — check availability for first stop
            availability, _ = TourAvailability.objects.get_or_create(
                tour=tour,
                fecha=date,
                defaults={'cupo_maximo': tour.cupo_maximo_diario}
            )

            if availability.cupo_disponible >= required_seats:
                availability.cupo_reservado += required_seats
                availability.save()
            
            self.object.status = SaleStatus.PENDING_APPROVAL
            self.object.save()
            
            passengers.instance = self.object
            passengers.save()
            
            _save_tour_stops(self.object, stops, pax)

            dest_label = "Multidestino" if len(stops) > 1 else "Único destino"
            if availability.cupo_disponible >= required_seats:
                messages.success(
                    self.request,
                    f"Venta {dest_label} registrada ({required_seats} cupos). Pendiente de confirmación logística."
                )
            else:
                messages.warning(
                    self.request,
                    f"Venta {dest_label} registrada, pero NO HAY CUPO SUFICIENTE. Pendiente de revisión."
                )

            return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear la venta. Revise los datos.")
        return super().form_invalid(form)


class SaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sales:list')

    def test_func(self):
        u = self.request.user
        # Admin and Logistics can edit any sale; Vendedores can edit only their own
        if getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA']:
            return True
        if u.role == 'VENDEDOR':
            sale = self.get_object()
            return sale.seller_id == u.pk
        return False

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'VENDEDOR':
            qs = qs.filter(seller=self.request.user)
        return qs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'VENDEDOR':
            # Block modifications to core fields for Vendedores visually
            disabled_fields = [
                'client_first_name', 'client_last_name', 'client_rut_passport', 
                'client_nationality', 'hotel_address', 'is_private', 'tour', 
                'tour_language', 'currency'
            ]
            for field in disabled_fields:
                if field in form.fields:
                    form.fields[field].widget.attrs['readonly'] = True
                    form.fields[field].widget.attrs['style'] = 'pointer-events: none; background-color: #e9ecef;'
            
            # Make total_amount visually readonly but allow JS submissions
            if 'total_amount' in form.fields:
                form.fields['total_amount'].widget.attrs['readonly'] = True
                
        return form

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['passengers'] = PassengerUpdateFormSet(self.request.POST, instance=self.object)
            data['existing_stops'] = json.dumps(_parse_tour_stops(self.request.POST), cls=DjangoJSONEncoder)
        else:
            data['passengers'] = PassengerUpdateFormSet(instance=self.object)
            # Pass existing tour stops for pre-population
            data['existing_stops'] = json.dumps(list(
                self.object.tour_stops.select_related('tour').values(
                    'id', 'tour_id', 'tour__name', 'tour_date', 'tour_language',
                    'is_private', 'private_description',
                    'pax_adults', 'pax_infants', 'price_adult', 'price_infant',
                    'subtotal', 'order'
                )
            ), cls=DjangoJSONEncoder)
        # Pass tour data as pre-serialised JSON
        from catalog.models import Tour as TourModel
        tours = TourModel.objects.filter(active=True).values(
            'id', 'name', 'precio_clp', 'precio_adulto_clp', 'precio_infante_clp',
            'precio_usd', 'precio_adulto_usd', 'precio_infante_usd',
            'precio_brl', 'precio_adulto_brl', 'precio_infante_brl'
        )
        data['tour_choices_json'] = json.dumps([
            {
                'id': str(t['id']),
                'name': t['name'],
                'precio_clp': float(t['precio_clp'] or 0),
                'precio_adulto_clp': float(t['precio_adulto_clp'] or 0),
                'precio_infante_clp': float(t['precio_infante_clp'] or 0),
                'precio_usd': float(t['precio_usd'] or 0),
                'precio_adulto_usd': float(t['precio_adulto_usd'] or 0),
                'precio_infante_usd': float(t['precio_infante_usd'] or 0),
                'precio_brl': float(t['precio_brl'] or 0),
                'precio_adulto_brl': float(t['precio_adulto_brl'] or 0),
                'precio_infante_brl': float(t['precio_infante_brl'] or 0),
            }
            for t in tours
        ])
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        passengers = context['passengers']

        # ── Validar formsets antes de procesos pesados ──
        if not passengers.is_valid():
            return self.render_to_response(self.get_context_data(form=form, passengers=passengers))

        # Enforce field locks for Vendedores only (Admin/Logistica skip this)
        if self.request.user.role == 'VENDEDOR' and not getattr(self.request.user, 'is_admin', False):
            orig = Sale.objects.get(pk=self.object.pk)
            form.instance.client_first_name = orig.client_first_name
            form.instance.client_last_name = orig.client_last_name
            form.instance.client_rut_passport = orig.client_rut_passport
            form.instance.client_nationality = orig.client_nationality
            form.instance.hotel_address = orig.hotel_address
            form.instance.is_private = orig.is_private
            form.instance.tour = orig.tour
            form.instance.tour_language = orig.tour_language
            form.instance.currency = orig.currency

        stops = _parse_tour_stops(self.request.POST)
        
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        for stop in stops:
            td = stop.get('tour_date')
            if td:
                try:
                    stop_date = datetime.datetime.strptime(td, '%Y-%m-%d').date()
                    if stop_date < today:
                        form.add_error(None, f"No puedes modificar la venta a un día en el pasado ({td}).")
                        return self.form_invalid(form)
                except ValueError:
                    pass

        try:
            pax = int(self.request.POST.get('passengers_count', 1))
        except (ValueError, TypeError):
            pax = 1

        with transaction.atomic():
            self.object = form.save()
            self.object.passengers_count = pax
            if stops:
                first = stops[0]
                if first.get('tour_id'):
                    try:
                        self.object.tour_id = int(first['tour_id'])
                    except (ValueError, TypeError):
                        pass
                self.object.tour_date = first.get('tour_date') or None
                self.object.tour_language = first.get('tour_language', 'ES')
                self.object.is_private = bool(first.get('is_private', False))
            self.object.save()
            
            passengers.instance = self.object
            passengers.save()
            
            _save_tour_stops(self.object, stops, pax)
            messages.success(self.request, "Venta actualizada correctamente.")
            return redirect(self.success_url)


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = 'sales/sale_confirm_delete.html'
    success_url = reverse_lazy('sales:list')

    def test_func(self):
        # Only Admin can delete sales
        u = self.request.user
        return u.is_authenticated and (getattr(u, 'is_admin', False) or u.role == 'ADMIN')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        seats_to_release = self.object.passengers_count

        if not self.object.is_private and self.object.tour:
            try:
                availability = TourAvailability.objects.get(
                    tour=self.object.tour, fecha=self.object.tour_date
                )
                availability.cupo_reservado -= seats_to_release
                if availability.cupo_reservado < 0:
                    availability.cupo_reservado = 0
                availability.save()
            except TourAvailability.DoesNotExist:
                pass

        return super().delete(request, *args, **kwargs)


# ============================================================
# ADMIN ACTION VIEWS
# ============================================================
from django.views import View
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings


class _AdminOrLogisticsRequired(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to restrict views to Admin and Logistics roles."""
    raise_exception = True

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA'])


class SaleConfirmView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Confirm a pending sale (PENDIENTE → CONFIRMADA)."""

    def test_func(self):
        u = self.request.user
        if getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA']:
            return True
        if u.role == 'VENDEDOR':
            sale = get_object_or_404(Sale, pk=self.kwargs.get('pk'))
            return sale.seller_id == u.pk
        return False

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        if sale.status == SaleStatus.PENDING_APPROVAL:
            sale.status = SaleStatus.CONFIRMED
            sale.confirmed_by = request.user
            sale.confirmed_at = timezone.now()
            sale.save(update_fields=['status', 'confirmed_by', 'confirmed_at'])
            messages.success(request, f"✅ Venta #{sale.pk} confirmada correctamente.")
        else:
            messages.warning(request, "Esta venta no se puede confirmar (ya está confirmada o cancelada).")
        return redirect(request.META.get('HTTP_REFERER', 'sales:detail'))


class SaleCancelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Cancel a sale (any status → CANCELADA)."""

    def test_func(self):
        u = self.request.user
        if getattr(u, 'is_admin', False) or u.role in ['ADMIN', 'LOGISTICA']:
            return True
        if u.role == 'VENDEDOR':
            sale = get_object_or_404(Sale, pk=self.kwargs.get('pk'))
            return sale.seller_id == u.pk
        return False

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        if sale.status == SaleStatus.CANCELLED:
            messages.warning(request, "Esta venta ya está cancelada.")
        else:
            reason = request.POST.get('cancellation_reason', '').strip()
            sale.status = SaleStatus.CANCELLED
            sale.cancellation_reason = reason
            sale.save(update_fields=['status', 'cancellation_reason'])
            messages.success(request, f"🚫 Venta #{sale.pk} cancelada.")
        return redirect(request.META.get('HTTP_REFERER', 'sales:detail'))


class SaleLogisticsAssignView(_AdminOrLogisticsRequired, View):
    """Assign vehicle, pickup time, and logistics notes to a confirmed sale."""

    def post(self, request, pk):
        from logistics.models import Vehicle
        sale = get_object_or_404(Sale, pk=pk)

        vehicle_id = request.POST.get('assigned_vehicle')
        pickup_time = request.POST.get('pickup_time') or None
        logistics_notes = request.POST.get('logistics_notes', '')

        if vehicle_id:
            try:
                sale.assigned_vehicle = Vehicle.objects.get(pk=int(vehicle_id))
            except (Vehicle.DoesNotExist, ValueError):
                sale.assigned_vehicle = None
        else:
            sale.assigned_vehicle = None

        sale.pickup_time = pickup_time
        sale.logistics_notes = logistics_notes
        sale.save(update_fields=['assigned_vehicle', 'pickup_time', 'logistics_notes'])
        messages.success(request, f"🚐 Logística de la Venta #{sale.pk} actualizada.")
        return redirect('sales:detail', pk=pk)


class SaleNotifyClientView(_AdminOrLogisticsRequired, View):
    """Send confirmation email + WhatsApp to the client."""

    def post(self, request, pk):
        from notifications.whatsapp import send_whatsapp_notification
        sale = get_object_or_404(Sale, pk=pk)

        if sale.status != SaleStatus.CONFIRMED:
            messages.error(request, "Solo se puede notificar clientes de ventas CONFIRMADAS.")
            return redirect('sales:detail', pk=pk)

        has_email = bool(sale.client_email)
        has_phone = bool(sale.client_phone)

        if not has_email and not has_phone:
            messages.error(request, "El cliente no tiene email ni teléfono registrado.")
            return redirect('sales:detail', pk=pk)

        # Determine which channels to use
        send_via = request.POST.get('send_via', 'both')  # email | whatsapp | both
        do_email = has_email and send_via in ('email', 'both')
        do_whatsapp = has_phone and send_via in ('whatsapp', 'both')

        # ── Determine stop to notify about ────────────────────────
        from sales.models import SaleTour
        from notifications.whatsapp import get_language_for_nationality
        stop_id = request.POST.get('stop_id')
        all_stops = sale.tour_stops.select_related('tour').order_by('order', 'id')
        if stop_id:
            try:
                selected_stops = [all_stops.get(pk=int(stop_id))]
            except (SaleTour.DoesNotExist, ValueError):
                selected_stops = list(all_stops)
        else:
            selected_stops = list(all_stops)

        # Use language based on client nationality
        lang = get_language_for_nationality(sale.client_nationality)

        # Build a stop label for the subject/flash messages
        if len(selected_stops) == 1:
            s = selected_stops[0]
            stop_label = f"{s.tour.name if s.tour else 'Tour'} — {s.tour_date.strftime('%d/%m/%Y') if s.tour_date else ''}"
        else:
            stop_label = None

        custom_message = request.POST.get('custom_message', '').strip()

        # ── Background Thread for Notifications ─────────────────────────────────────
        import threading
        import logging
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings as django_settings

        logger = logging.getLogger(__name__)

        def enviar_notificaciones_cliente(sale_obj, stops_list, do_em, do_wa, lang_code, custom_msg, stop_lbl):
            # Emails
            if do_em:
                context = {
                    'sale': sale_obj,
                    'stops': stops_list,
                    'passengers': sale_obj.passengers.all(),
                    'lang': lang_code,
                    'custom_message': custom_msg,
                }
                _subjects = {
                    'EN': f"✈️ Booking Confirmed #{sale_obj.pk}{' — ' + stop_lbl if stop_lbl else ''} — Getaway Chile",
                    'PT': f"✈️ Reserva Confirmada #{sale_obj.pk}{' — ' + stop_lbl if stop_lbl else ''} — Getaway Chile",
                    'ES': f"✈️ Confirmación de Reserva #{sale_obj.pk}{' — ' + stop_lbl if stop_lbl else ''} — Getaway Chile",
                }
                subject = _subjects.get(lang_code, _subjects['ES'])
                html_message = render_to_string('sales/email_client_confirmation.html', context)
                plain_message = (
                    f"Hola {sale_obj.client_first_name},\n\n"
                    f"Tu reserva #{sale_obj.pk} ha sido CONFIRMADA.\n"
                    f"Hora de recogida: {sale_obj.pickup_time or 'Por confirmar'}\n"
                    f"Hotel/Dirección: {sale_obj.hotel_address or 'Sin especificar'}\n\n"
                    + (f"Observaciones: {custom_msg}\n\n" if custom_msg else "") +
                    f"¡Muchas gracias por elegir Getaway Chile!"
                )
                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        html_message=html_message,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[sale_obj.client_email],
                        fail_silently=False,
                    )
                    logger.info(f"Email asíncrono enviado con éxito a {sale_obj.client_email}")
                except Exception as e:
                    logger.error(f"Error asíncrono al enviar email a {sale_obj.client_email}: {e}")

            # WhatsApp
            if do_wa:
                try:
                    from notifications.whatsapp import send_whatsapp_notification_for_stops
                    ok, detail = send_whatsapp_notification_for_stops(sale_obj, stops_list, lang_code, custom_msg)
                    if not ok:
                        logger.warning(f"Error asíncrono WhatsApp para {sale_obj.client_phone}: {detail}")
                    else:
                        logger.info(f"WhatsApp asíncrono enviado con éxito a {sale_obj.client_phone}")
                except Exception as e:
                    logger.error(f"Error de código al enviar WhatsApp a {sale_obj.client_phone}: {e}")

        # Iniciar hilo
        thread = threading.Thread(
            target=enviar_notificaciones_cliente,
            args=(sale, selected_stops, do_email, do_whatsapp, lang, custom_message, stop_label)
        )
        thread.daemon = True
        thread.start()

        messages.success(request, f"¡Las notificaciones para el cliente están siendo procesadas en segundo plano! 🚀")

        # ── Mark as notified ───────────────────────────────────────
        sale.client_notified = True
        sale.client_notified_at = timezone.now()
        sale.save(update_fields=['client_notified', 'client_notified_at'])

        return redirect('sales:detail', pk=pk)



# -- Per-stop confirmation / cancellation ---------------------------------------

class StopConfirmView(_AdminOrLogisticsRequired, View):
    """Confirm a single SaleTour stop independently."""

    def post(self, request, sale_pk, stop_pk):
        stop = get_object_or_404(SaleTour, pk=stop_pk, sale_id=sale_pk)
        if stop.stop_status == SaleTour.StopStatus.CONFIRMED:
            messages.info(request, f"El stop ya estaba confirmado.")
            return redirect('sales:detail', pk=sale_pk)

        stop.stop_status = SaleTour.StopStatus.CONFIRMED
        stop.stop_confirmed_at = timezone.now()
        stop.stop_confirmed_by = request.user
        stop.stop_cancellation_reason = ''
        stop.save(update_fields=['stop_status', 'stop_confirmed_at', 'stop_confirmed_by', 'stop_cancellation_reason'])

        tour_label = stop.tour.name if stop.tour else 'Tour Privado'
        date_label = stop.tour_date.strftime('%d/%m/%Y') if stop.tour_date else ''
        messages.success(request, f"Stop '{tour_label} {date_label}' CONFIRMADO.")
        return redirect('sales:detail', pk=sale_pk)


class StopCancelView(_AdminOrLogisticsRequired, View):
    """Cancel a single SaleTour stop independently."""

    def post(self, request, sale_pk, stop_pk):
        stop = get_object_or_404(SaleTour, pk=stop_pk, sale_id=sale_pk)
        reason = request.POST.get('stop_cancel_reason', '').strip()

        stop.stop_status = SaleTour.StopStatus.CANCELLED
        stop.stop_cancellation_reason = reason
        stop.save(update_fields=['stop_status', 'stop_cancellation_reason'])

        tour_label = stop.tour.name if stop.tour else 'Tour Privado'
        date_label = stop.tour_date.strftime('%d/%m/%Y') if stop.tour_date else ''
        messages.warning(request, f"Stop '{tour_label} {date_label}' CANCELADO.")
        return redirect('sales:detail', pk=sale_pk)


# ============================================================
# VENDEDOR-EXCLUSIVE SALE MANAGEMENT VIEWS
# ============================================================

class _VendedorOwnerRequired(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin: Only for VENDEDOR who owns the sale. 403 for all other roles."""
    raise_exception = True

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated or u.role != 'VENDEDOR':
            return False
        sale = get_object_or_404(Sale, pk=self.kwargs.get('pk'))
        return sale.seller_id == u.pk


class VendedorSaleManageView(_VendedorOwnerRequired, View):
    """
    Exclusive Vendedor dashboard to manage their own sale:
    - View sale details (read-only)
    - Confirm the sale
    - Cancel the sale with a reason
    - Add observations/notes for logistics
    """
    template_name = 'sales/vendedor_sale_manage.html'

    def get(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        ctx = {
            'sale': sale,
            'stops': sale.tour_stops.select_related('tour').order_by('order', 'id'),
            'passengers': sale.passengers.all(),
            'can_confirm': sale.status == SaleStatus.PENDING_APPROVAL,
            'can_cancel': sale.status != SaleStatus.CANCELLED,
        }
        return render(request, self.template_name, ctx)


class VendedorSaleObservationsView(_VendedorOwnerRequired, View):
    """POST only: Vendedor saves internal observations for logistics."""

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated or u.role != 'VENDEDOR':
            return False
        sale = get_object_or_404(Sale, pk=self.kwargs.get('pk'))
        return sale.seller_id == u.pk

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        observations = request.POST.get('logistics_notes', '').strip()
        sale.logistics_notes = observations
        sale.save(update_fields=['logistics_notes'])
        messages.success(request, "📝 Observaciones guardadas para el equipo de logística.")
        return redirect('sales:vendedor_manage', pk=pk)
