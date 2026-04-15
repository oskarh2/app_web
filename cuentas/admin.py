# cuentas/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    list_display = ['perfil_id', 'email', 'first_name', 'last_name', 'role', 'empresa', 'is_active']
    list_filter = ['role', 'is_active', 'fecha_registro']
    search_fields = ['email', 'first_name', 'last_name', 'perfil_id']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Información de Negocio', {'fields': ('empresa',)}),
        ('Fechas Importantes', {'fields': ('last_login', 'fecha_registro', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role', 'empresa'),
        }),
    )
    
    readonly_fields = ['perfil_id', 'fecha_registro', 'created_at']
    ordering = ['-perfil_id']

admin.site.register(Usuario, UsuarioAdmin)