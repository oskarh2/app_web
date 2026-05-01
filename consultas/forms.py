# consultas/forms.py (agrega al final)
from django import forms
from .models import ValidacionArchivo

class ArchivoCSVForm(forms.Form):
    """Formulario para cargar archivo CSV"""
    archivo = forms.FileField(
        label='Archivo CSV',
        help_text='El archivo debe tener el formato: NAME,LASTNAME,TIPO,ID,FECHA-EXP,CITY',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )

# consultas/forms.py


class DatosManualForm(forms.Form):
    """Formulario para ingreso manual de datos ajustado para el Agente Dual"""
    NAME = forms.CharField(
        max_length=100,
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Ej: NESTOR GREGORIO'})
    )
    LASTNAME = forms.CharField(
        max_length=100,
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Ej: VERA FERNANDEZ'})
    )
    tipo_documento = forms.ChoiceField(
        choices=[('CC', 'Cédula de Ciudadanía'), ('CE', 'Cédula de Extranjería'), ('PA', 'Pasaporte')],
        label='Tipo de Documento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ID = forms.CharField(
        max_length=20,
        label='Número de Documento',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 80167962'})
    )
    FECHA_EXP = forms.DateField(
        required=False,
        label='Fecha de Expedición',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    ciudad = forms.CharField(
        max_length=100,
        required=False,
        label='Ciudad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: BOGOTA'})
    )