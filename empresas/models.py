import uuid
from django.db import models
from django.contrib.auth.models import User

class Empresa(models.Model):
    codigo = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    nombre = models.CharField(max_length=255)
    nit = models.CharField(max_length=50, unique=True)
    direccion = models.TextField(blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'empresas'
        ordering = ['-created_at']
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.nombre
