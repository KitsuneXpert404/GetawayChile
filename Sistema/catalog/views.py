from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Tour
from .forms import TourForm

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role == 'ADMIN' or self.request.user.role == 'LOGISTICA')

from django.views.generic import DetailView

class TourDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Tour
    template_name = 'catalog/tour_detail.html'
    context_object_name = 'tour'


class TourListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Tour
    template_name = 'catalog/tour_list.html'
    context_object_name = 'tours'
    ordering = ['name']

class TourCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Tour
    form_class = TourForm
    template_name = 'catalog/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def form_valid(self, form):
        messages.success(self.request, "Tour creado exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        error_msg = "Error al crear el tour."
        for field, errors in form.errors.items():
            for error in errors:
                error_msg += f" [{field}: {error}]"
        messages.error(self.request, error_msg)
        return super().form_invalid(form)

class TourUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Tour
    form_class = TourForm
    template_name = 'catalog/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def form_valid(self, form):
        messages.success(self.request, "Tour actualizado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        error_msg = "Error al actualizar el tour."
        for field, errors in form.errors.items():
            for error in errors:
                error_msg += f" [{field}: {error}]"
        messages.error(self.request, error_msg)
        return super().form_invalid(form)

class TourDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Tour
    template_name = 'catalog/tour_confirm_delete.html'
    success_url = reverse_lazy('tour_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Tour eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
