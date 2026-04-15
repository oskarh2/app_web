from django import forms
from .models import PageTracking

class PageTrackingForm(forms.ModelForm):
    class Meta:
        model = PageTracking
        fields = ['page', 'type', 'kind', 'steps', 'status', 'user_id', 'metadata']
        widgets = {
            'page': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: dashboard, profile, settings'
            }),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'steps': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"step1": "completed", "step2": "pending"}'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'user_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID del usuario (perfil_id)'
            }),
            'metadata': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"key": "value"}'
            }),
        }
    
    def clean_page(self):
        page = self.cleaned_data.get('page')
        if page and len(page) > 20:
            raise forms.ValidationError('Page name cannot exceed 20 characters')
        return page
    
    def clean_steps(self):
        steps = self.cleaned_data.get('steps')
        if isinstance(steps, str):
            try:
                import json
                steps = json.loads(steps)
            except json.JSONDecodeError:
                raise forms.ValidationError('Invalid JSON format')
        return steps
    
    def clean_metadata(self):
        metadata = self.cleaned_data.get('metadata')
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise forms.ValidationError('Invalid JSON format')
        return metadata