import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from .models import Ticket, TicketStatus
from .forms import TicketCreateForm, TicketRespondForm


RESPONDER_ROLES = ['ADMIN', 'LOGISTICA']

class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('creator', 'responded_by', 'tour')

        if user.role in RESPONDER_ROLES:
            # ADMIN and LOGISTICA see tickets directed to their role + their own created tickets
            qs = qs.filter(
                Q(target_role=user.role) | Q(creator=user)
            )
        else:
            # Everyone else (VENDEDOR, CONDUCTOR, DESARROLLADOR) sees only their own
            qs = qs.filter(creator=user)

        status_filter = self.request.GET.get('status', '')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = TicketStatus.choices
        context['current_status'] = self.request.GET.get('status', '')
        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(self.request, "Solicitud enviada correctamente.")
        return super().form_valid(form)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('creator', 'responded_by', 'tour')
        if user.role in RESPONDER_ROLES:
            return qs.filter(Q(target_role=user.role) | Q(creator=user))
        return qs.filter(creator=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.role in RESPONDER_ROLES and self.object.is_open:
            context['respond_form'] = TicketRespondForm(initial={
                'new_status': 'EN_REVISION'
            })
        return context


@login_required
def ticket_respond(request, pk):
    user = request.user
    if user.role not in RESPONDER_ROLES:
        messages.error(request, "No tienes permiso para responder tickets.")
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk, target_role=user.role)
    if request.method == 'POST':
        form = TicketRespondForm(request.POST)
        if form.is_valid():
            ticket.response = form.cleaned_data['response']
            ticket.status = form.cleaned_data['new_status']
            ticket.responded_by = user
            ticket.responded_at = datetime.datetime.now()
            ticket.save()
            messages.success(request, f"Ticket #{ticket.id} actualizado a '{ticket.get_status_display()}'.")
    return redirect('tickets:detail', pk=pk)
