from django import forms
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'nit', 'direccion', 'pais', 'activo', 'metadata']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '900.123.456-7'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '{"clave": "valor"}'}),
        }
