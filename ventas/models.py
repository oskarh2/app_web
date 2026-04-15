from django.db import models

class Venta(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE, related_name='ventas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad = models.PositiveIntegerField(default=0)
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ventas'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Venta {self.empresa} ({self.fecha_inicio})"
