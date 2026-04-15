# cuentas/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Max
import uuid

class UsuarioManager(BaseUserManager):
    """Custom manager for Usuario model using perfil_id as primary key"""
    
    def _get_next_perfil_id(self):
        """Get the next available perfil_id"""
        max_id = Usuario.objects.aggregate(Max('perfil_id'))['perfil_id__max']
        return (max_id + 1) if max_id is not None else 1
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        
        # Auto-generate perfil_id if not provided
        if 'perfil_id' not in extra_fields or extra_fields['perfil_id'] is None:
            extra_fields['perfil_id'] = self._get_next_perfil_id()
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Model for usuarios table that integrates with Django auth
    """
    perfil_id = models.IntegerField(primary_key=True, db_column='perfil_id')
    empresa = models.UUIDField(
        null=True, 
        blank=True, 
        db_column='empresa',
        help_text="UUID de la empresa (relacionado con empresas.codigo)"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, 
        db_column='fecha_registro'
    )
    role = models.CharField(
        max_length=50, 
        default='user', 
        db_column='role',
        choices=[
            ('admin', 'Administrador'),
            ('user', 'Usuario'),
            ('viewer', 'Visitante'),
        ]
    )
    last_login = models.DateTimeField(
        null=True, 
        blank=True, 
        db_column='last_login'
    )
    is_active = models.BooleanField(
        default=True, 
        db_column='is_active'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        db_column='created_at'
    )
    
    # Required fields for Django auth
    email = models.EmailField(unique=True, db_column='email')
    first_name = models.CharField(max_length=150, blank=True, db_column='first_name')
    last_name = models.CharField(max_length=150, blank=True, db_column='last_name')
    
    # Django auth required fields
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'usuarios'
        managed = False  # Don't let Django modify the existing table
        ordering = ['-perfil_id']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def save(self, *args, **kwargs):
        """Override save to ensure perfil_id is set"""
        if not self.perfil_id:
            # Get the max perfil_id and add 1
            max_id = Usuario.objects.aggregate(Max('perfil_id'))['perfil_id__max']
            self.perfil_id = (max_id + 1) if max_id is not None else 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})" if self.get_full_name() else self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name or self.email
    
    def has_perm(self, perm, obj=None):
        # Admin users have all permissions
        if self.role == 'admin' or self.is_superuser:
            return True
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        if self.role == 'admin' or self.is_superuser:
            return True
        return super().has_module_perms(app_label)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_empresa_object(self):
        """Get the Empresa object related to this user"""
        from empresas.models import Empresa
        if self.empresa:
            try:
                return Empresa.objects.get(codigo=self.empresa)
            except Empresa.DoesNotExist:
                pass
        return None