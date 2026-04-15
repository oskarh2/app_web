# cuentas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Usuario
from .forms import (
    UsuarioLoginForm, UsuarioCreationForm, 
    UsuarioProfileForm, UsuarioAdminForm
)
from empresas.models import Empresa

# Funciones auxiliares para verificar roles
def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

def is_user_or_admin(user):
    """Check if user is regular user or admin"""
    return user.is_authenticated and user.role in ['admin', 'user']

def is_viewer_or_higher(user):
    """Check if user is at least viewer"""
    return user.is_authenticated

# Vista de login corregida
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('cuentas:perfil')
    
    if request.method == 'POST':
        form = UsuarioLoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'✅ ¡Bienvenido {user.get_full_name()}!')
                
                next_url = request.GET.get('next', 'cuentas:perfil')
                return redirect(next_url)
            else:
                messages.error(request, '❌ Credenciales inválidas')
        else:
            messages.error(request, '❌ Por favor corrige los errores')
    else:
        form = UsuarioLoginForm()
    
    return render(request, 'cuentas/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, '✅ Sesión cerrada correctamente')
    return redirect('cuentas:login')

def register_view(request):
    """User registration view - Solo admins pueden crear usuarios"""
    if not is_admin(request.user):
        messages.error(request, '❌ No tienes permiso para crear usuarios')
        return redirect('cuentas:perfil')
    
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'✅ ¡Usuario {user.email} creado exitosamente!')
            return redirect('cuentas:lista_usuarios')
        else:
            messages.error(request, '❌ Por favor corrige los errores')
    else:
        form = UsuarioCreationForm()
    
    empresas = Empresa.objects.all()
    return render(request, 'cuentas/registro.html', {
        'form': form,
        'empresas': empresas
    })

@login_required
def perfil_view(request):
    """User profile view - Accesible para todos los usuarios autenticados"""
    return render(request, 'cuentas/perfil.html', {'usuario': request.user})

@login_required
def editar_perfil_view(request):
    """Edit user profile - Solo el propio usuario puede editar su perfil"""
    if request.method == 'POST':
        form = UsuarioProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Perfil actualizado correctamente')
            return redirect('cuentas:perfil')
        else:
            messages.error(request, '❌ Por favor corrige los errores')
    else:
        form = UsuarioProfileForm(instance=request.user)
    
    return render(request, 'cuentas/editar_perfil.html', {'form': form})

@login_required
@user_passes_test(is_admin)  # Solo administradores
def lista_usuarios(request):
    """Admin view to list all users"""
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    queryset = Usuario.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role_filter:
        queryset = queryset.filter(role=role_filter)
    
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'roles': Usuario._meta.get_field('role').choices,
        'user_role': request.user.role,  # Para usar en el template
    }
    return render(request, 'cuentas/lista_usuarios.html', context)

@login_required
@user_passes_test(is_admin)
def editar_usuario(request, perfil_id):
    """Admin view to edit user - Solo admins"""
    usuario = get_object_or_404(Usuario, pk=perfil_id)
    
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Usuario {usuario.email} actualizado')
            return redirect('cuentas:lista_usuarios')
        else:
            messages.error(request, '❌ Por favor corrige los errores')
    else:
        form = UsuarioAdminForm(instance=usuario)
    
    return render(request, 'cuentas/editar_usuario.html', {
        'form': form,
        'usuario': usuario
    })

@login_required
@user_passes_test(is_admin)
def cambiar_estado_usuario(request, perfil_id):
    """Admin view to activate/deactivate user - Solo admins"""
    usuario = get_object_or_404(Usuario, pk=perfil_id)
    
    # Evitar que un admin se desactive a sí mismo
    if usuario.perfil_id == request.user.perfil_id:
        messages.error(request, '❌ No puedes cambiar tu propio estado')
        return redirect('cuentas:lista_usuarios')
    
    if request.method == 'POST':
        usuario.is_active = not usuario.is_active
        usuario.save()
        estado = "activado" if usuario.is_active else "desactivado"
        messages.success(request, f'✅ Usuario {usuario.email} {estado}')
    
    return redirect('cuentas:lista_usuarios')