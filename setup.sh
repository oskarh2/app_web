#!/bin/bash
echo "🔧 Verificando estructura de archivos..."

# Verificar si existe settings.py
if [ -f config/settings.py ]; then
    export DJANGO_SETTINGS_MODULE=config.settings
    echo "✅ Configuración detectada: config.settings"
else
    mkdir -p config/settings
    touch config/settings/__init__.py
    
    echo "✨ Creando configuración base..."
    
    # Guardar variables actuales antes de cambiar
    OLD_ENV=$(cat .env 2>/dev/null)
    
    cat > .env << EOFENV
DJANGO_SETTINGS_MODULE=config.settings.base
DEBUG=True
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DB_NAME=gestor_consultas
DB_USER=app_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
EOFENV
    
    # Crear settings/base.py
    cat > config/settings/base.py << 'EOFBASE'
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1')
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cuentas.apps.CuentasConfig',
    'empresas.apps.EmpresasConfig',
    'scrapying.apps.ScrapyingConfig',
    'consultas.apps.ConsultasConfig',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'gestor_consultas'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
TIME_ZONE = 'America/Bogota'
USE_TZ = True
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
ALLOWED_HOSTS = ['*']
EOFBASE

    echo "✅ Configuración base creada"
    export DJANGO_SETTINGS_MODULE=config.settings.base
fi

echo "🚀 Intentando configurar Django..."
export PATH="$OLD_ENV:$PATH" 2>/dev/null || true
python manage.py check --verbosity=2

echo "✅ Prueba final"
python manage.py showmigrations
