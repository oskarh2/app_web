from .base import *

DEBUG = True
SECRET_KEY = 'tu_clave_secreta_local_segura'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gestor_consultas',
        'USER': 'app_user',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
