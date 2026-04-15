# cuentas/urls.py
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from . import views

app_name = 'cuentas'

def admin_redirect(request):
    """Redirige a lista de usuarios solo si es admin, sino al perfil"""
    if request.user.is_authenticated and (request.user.role == 'admin' or request.user.is_superuser):
        return redirect('cuentas:lista_usuarios')
    elif request.user.is_authenticated:
        return redirect('cuentas:perfil')
    else:
        return redirect('cuentas:login')

urlpatterns = [
    # Ruta raíz con verificación de admin
    path('', admin_redirect, name='index'),
    
    # Tus otras URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.register_view, name='registro'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:perfil_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:perfil_id>/toggle/', views.cambiar_estado_usuario, name='cambiar_estado'),
]