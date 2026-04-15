from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings  # 👈 Import settings here

# config/urls.py - Add this line
from django.views.generic import RedirectView


def home(request):
    """Dashboard home page"""
    apps = [
        {
            'name': 'Cuentas',
            'url': '/cuentas/usuarios/', 
            'icon': 'bi-people',
            'desc': 'Gestión de usuarios y autenticación',
            'color': 'primary'
        },
        {
            'name': 'Empresas',
            'url': '/empresas/',
            'icon': 'bi-building',
            'desc': 'Administración de empresas y ventas',
            'color': 'success'
        },
        {
            'name': 'Scraps',
            'url': '/scraps/',
            'icon': 'bi-bug',
            'desc': 'Page tracking y web scraping',
            'color': 'warning'
        },
        {
            'name': 'Consultas',
            'url': '/consultas/validador/',
            'icon': 'bi-folder',
            'desc': 'Consultas, archivos y detalles',
            'color': 'info'
        },
    ]
    # 👇 Pass settings to template explicitly
    return render(request, 'home.html', {'apps': apps, 'settings': settings})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # 👈 Root URL
    path('cuentas/', include(('cuentas.urls', 'cuentas'), namespace='cuentas')),
    path('empresas/', include(('empresas.urls', 'empresas'), namespace='empresas')),
    path('scraps/', include(('scrapying.urls', 'scraps'), namespace='scraps')),
    path('consultas/', include(('consultas.urls', 'consultas'), namespace='consultas')),
     path('accounts/login/', RedirectView.as_view(url='/cuentas/login/', permanent=True)),
    path('accounts/logout/', RedirectView.as_view(url='/cuentas/logout/', permanent=True)),
  
]
