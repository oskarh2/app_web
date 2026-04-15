# consultas/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

app_name = 'consultas'


urlpatterns = [
    # URLs existentes...
    path('', RedirectView.as_view(pattern_name='consultas:validador_index', permanent=False), name='index'),
    path('validador/', views.validador_index, name='validador_index'),
    path('validador/cargar-archivo/', views.cargar_archivo, name='cargar_archivo'),
    path('validador/ingresar-manual/', views.ingresar_manual, name='ingresar_manual'),
    path('validador/lista-validaciones/', views.lista_validaciones, name='lista_validaciones'),
    path('validador/validacion/<int:validacion_id>/', views.detalle_validacion, name='detalle_validacion'),
    path('validador/registro/<int:registro_id>/', views.detalle_registro, name='detalle_registro'),
    
    # Vistas de recuperación de contraseña
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='consultas/password_reset.html',
             email_template_name='consultas/password_reset_email.html',
             subject_template_name='consultas/password_reset_subject.txt',
             success_url='/consultas/password-reset/done/'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='consultas/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='consultas/password_reset_confirm.html',
             success_url='/consultas/password-reset/complete/'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='consultas/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]