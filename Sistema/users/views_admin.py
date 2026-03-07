from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm

User = get_user_model()

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'core/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determine the base template based on the user's role
        if user.role == 'VENDEDOR':
            context['role_base_template'] = 'core/base_vendedor.html'
        elif user.role == 'LOGISTICA':
            context['role_base_template'] = 'core/base_logistica.html'
        elif user.role == 'CONDUCTOR':
            context['role_base_template'] = 'core/base_conductor.html'
        else:
            context['role_base_template'] = 'core/base_dashboard.html'
            
        return context

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        messages.success(self.request, f"Usuario creado exitosamente. Email institucional: {form.instance.email}")
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserUpdateForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'core/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Prevent self-deletion
        if self.object == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta.")
            return redirect('user_list')
            
        messages.success(self.request, "Usuario eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages

class UserChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'core/password_change_form.html'
    success_url = reverse_lazy('dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determine the base template based on the user's role
        if user.role == 'VENDEDOR':
            context['role_base_template'] = 'core/base_vendedor.html'
        elif user.role == 'LOGISTICA':
            context['role_base_template'] = 'core/base_logistica.html'
        elif user.role == 'CONDUCTOR':
            context['role_base_template'] = 'core/base_conductor.html'
        else:
            context['role_base_template'] = 'core/base_dashboard.html'
            
        return context
    
    def form_valid(self, form):
        # Update user flag
        user = self.request.user
        user.requires_password_change = False
        user.save()
        messages.success(self.request, "Contraseña actualizada correctamente.")
        return super().form_valid(form)

from django.views.generic import UpdateView

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'second_name', 'last_name', 'second_last_name', 'phone', 'personal_email', 'rut', 'birth_date', 'photo']
    template_name = 'core/user_profile.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determine the base template based on the user's role
        if user.role == 'VENDEDOR':
            context['role_base_template'] = 'core/base_vendedor.html'
        elif user.role == 'LOGISTICA':
            context['role_base_template'] = 'core/base_logistica.html'
        elif user.role == 'CONDUCTOR':
            context['role_base_template'] = 'core/base_conductor.html'
        else:
            context['role_base_template'] = 'core/base_dashboard.html'
            
        return context

    def form_valid(self, form):
        messages.success(self.request, "Tu perfil ha sido actualizado.")
        return super().form_valid(form)
