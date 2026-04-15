from django.urls import path
from . import views

app_name = 'scrapying'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('crear/', views.crear, name='crear'),
    path('<uuid:tracking_id>/', views.detalle, name='detalle'),
    path('<uuid:tracking_id>/editar/', views.editar, name='editar'),
    path('<uuid:tracking_id>/eliminar/', views.eliminar, name='eliminar'),
    path('<uuid:tracking_id>/estado/', views.actualizar_estado, name='actualizar_estado'),
    path('actualizar-masivo/', views.actualizar_masivo, name='actualizar_masivo'),
    path('exportar-csv/', views.exportar_csv, name='exportar_csv'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('api/lista/', views.api_lista, name='api_lista'),
    path('<uuid:tracking_id>/duplicar/', views.duplicar, name='duplicar'),
]
