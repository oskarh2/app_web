from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('crear/', views.crear, name='crear'),
    path('<uuid:pk>/editar/', views.editar, name='editar'),
    path('<uuid:pk>/eliminar/', views.eliminar, name='eliminar'),
]
