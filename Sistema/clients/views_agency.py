from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import AdminOrLogisticsRequiredMixin
from django.contrib import messages
from .models import Agency
from .forms import AgencyForm

class AgencyListView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, ListView):
    model = Agency
    template_name = 'clients/agency_list.html'
    context_object_name = 'agencies'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

class AgencyCreateView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, CreateView):
    model = Agency
    form_class = AgencyForm
    template_name = 'clients/agency_form.html'
    success_url = reverse_lazy('agency-list')

    def form_valid(self, form):
        messages.success(self.request, "Agencia creada exitosamente.")
        return super().form_valid(form)

class AgencyUpdateView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, UpdateView):
    model = Agency
    form_class = AgencyForm
    template_name = 'clients/agency_form.html'
    success_url = reverse_lazy('agency-list')

    def form_valid(self, form):
        messages.success(self.request, "Agencia actualizada exitosamente.")
        return super().form_valid(form)

class AgencyDeleteView(LoginRequiredMixin, AdminOrLogisticsRequiredMixin, DeleteView):
    model = Agency
    template_name = 'clients/agency_confirm_delete.html'
    success_url = reverse_lazy('agency-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Agencia eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
