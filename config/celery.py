import os
from celery import Celery

# Reemplaza 'config.settings' por la ruta a tus settings si es diferente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Forzar explícitamente el broker a Redis en el constructor
app = Celery('validador_project', 
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

# Esto lee el resto de configuraciones que empiecen con CELERY_ en settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()