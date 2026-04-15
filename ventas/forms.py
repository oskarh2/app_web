from django import forms
from .models import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['empresa', 'fecha_inicio', 'fecha_fin', 'cantidad', 'monto_total']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'monto_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
