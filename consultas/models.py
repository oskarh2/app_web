# consultas/models.py (agrega estos modelos al final)
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ValidacionArchivo(models.Model):
    """Modelo para almacenar información de archivos procesados"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='validaciones_archivos')
    nombre_archivo = models.CharField(max_length=255)
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    total_registros = models.IntegerField(default=0)
    registros_exitosos = models.IntegerField(default=0)
    registros_fallidos = models.IntegerField(default=0)
    archivo = models.FileField(upload_to='validaciones/archivos/', null=True, blank=True)
    
    class Meta:
        db_table = 'validaciones_archivo'
        verbose_name = 'Validación de Archivo'
        verbose_name_plural = 'Validaciones de Archivos'
        ordering = ['-fecha_procesamiento']
    
    def __str__(self):
        return f"{self.nombre_archivo} - {self.fecha_procesamiento.strftime('%Y-%m-%d %H:%M')}"

class RegistroValidacion(models.Model):
    """Modelo para almacenar cada registro procesado"""
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('PA', 'Pasaporte'),
    ]
    
    ESTADO_CHOICES = [
        ('exitoso', 'Exitoso'),
        ('fallido', 'Fallido'),
        ('pendiente', 'Pendiente'),
    ]
    
    validacion = models.ForeignKey(ValidacionArchivo, on_delete=models.CASCADE, related_name='registros')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(max_length=20)
    fecha_expedicion = models.DateField(null=True, blank=True)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    mensaje_respuesta = models.TextField(blank=True, null=True)
    respuesta_json = models.JSONField(null=True, blank=True)  # Guardar respuesta completa del WS
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'registros_validacion'
        verbose_name = 'Registro de Validación'
        verbose_name_plural = 'Registros de Validaciones'
        ordering = ['-fecha_procesamiento']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.tipo_documento}: {self.numero_documento}"