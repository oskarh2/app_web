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

class DatosManualForm(forms.Form):
    """Formulario para ingreso manual de datos"""
    nombre = forms.CharField(
        max_length=100,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: NESTOR GREGORIO'})
    )
    apellido = forms.CharField(
        max_length=100,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: VERA FERNANDEZ'})
    )
    tipo_documento = forms.ChoiceField(
        choices=[
            ('CC', 'Cédula de Ciudadanía (CC)'),
            ('CE', 'Cédula de Extranjería (CE)'),
            ('TI', 'Tarjeta de Identidad (TI)'),
            ('PA', 'Pasaporte (PA)'),
        ],
        label='Tipo de Documento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    numero_documento = forms.CharField(
        max_length=20,
        label='Número de Documento',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 80167962'})
    )
    fecha_expedicion = forms.DateField(
        required=False,
        label='Fecha de Expedición',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    ciudad = forms.CharField(
        max_length=100,
        label='Ciudad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: BOGOTA'})
    )