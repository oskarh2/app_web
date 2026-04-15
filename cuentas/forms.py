# cuentas/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import Usuario
from empresas.models import Empresa  # 👈 Agrega esta importación

class UsuarioCreationForm(UserCreationForm):
    """Form for creating new users"""
    
    # Agrega campo para seleccionar empresa
    empresa_select = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        required=False,
        label="Empresa",
        help_text="Selecciona la empresa a la que pertenece el usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'role', 'empresa_select')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar campos de password
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Generar perfil_id si no existe
        if not user.perfil_id:
            from django.db.models import Max
            max_id = Usuario.objects.aggregate(Max('perfil_id'))['perfil_id__max']
            user.perfil_id = (max_id + 1) if max_id is not None else 1
        
        # Asignar el UUID de la empresa seleccionada
        empresa_obj = self.cleaned_data.get('empresa_select')
        if empresa_obj:
            user.empresa = empresa_obj.codigo  # Asigna el UUID
        else:
            user.empresa = None
        
        if commit:
            user.save()
        return user

# Mantén el resto de tus formas igual...
class UsuarioAdminForm(UserChangeForm):
    """Form for admin to edit users"""
    
    empresa_select = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        required=False,
        label="Empresa",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'empresa_select')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-seleccionar la empresa actual del usuario
        if self.instance and self.instance.empresa:
            try:
                empresa_obj = Empresa.objects.get(codigo=self.instance.empresa)
                self.fields['empresa_select'].initial = empresa_obj
            except Empresa.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Asignar el UUID de la empresa seleccionada
        empresa_obj = self.cleaned_data.get('empresa_select')
        if empresa_obj:
            user.empresa = empresa_obj.codigo
        else:
            user.empresa = None
        
        if commit:
            user.save()
        return user

# El resto de tus formas continúan igual...
class UsuarioProfileForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

class UsuarioLoginForm(forms.Form):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Email o contraseña incorrectos")
            if not user.is_active:
                raise forms.ValidationError("Esta cuenta está desactivada")
        return cleaned_data