# config/context_processors.py
from datetime import datetime
import django

def global_variables(request):
    """Add global variables to all templates"""
    return {
        'now': datetime.now(),
        'django_version': django.get_version(),
    }