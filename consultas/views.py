# consultas/views.py (agrega al final)
import csv
import io
import os
import sys
from django.conf import settings
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ValidacionArchivo, RegistroValidacion
from .forms import ArchivoCSVForm, DatosManualForm
from .services import WebServiceCliente
from django.http import HttpResponse, Http404, HttpResponseForbidden
from consultas.tasks import procesar_csv_background
import requests




# 2. Aseguramos que 'utils' sea lo primero que Python revise
utils_path = os.path.join(settings.BASE_DIR, 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path) # Usamos insert(0) para darle máxima prioridad

# 3. Importamos usando el espacio de nombres de la carpeta
# Importaciones con los nombres corregidos
# 2. Importaciones corregidas (SIN etiquetas de texto como)
import database
import scraping_config as config_scraping
from main import process_person, set_service_url



@login_required
def validador_index(request):
    """Página principal del validador"""
    context = {
        'titulo': 'Validador de Documentos',
        'validaciones_recientes': ValidacionArchivo.objects.filter(
            usuario=request.user
        )[:5]
    }
    return render(request, 'consultas/validador_index.html', context)



@login_required
def cargar_archivo(request):
    if request.method == 'POST':
        form = ArchivoCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo_subido = request.FILES['archivo']
            nombre_usuario_str = request.user.get_username()
            
            # 1. Creamos el registro maestro pero SIN procesar filas aún
            validacion = ValidacionArchivo.objects.create(
                usuario=request.user,
                nombre_archivo=archivo_subido.name,
                archivo=archivo_subido
            )

            # 2. LANZAR TAREA A CELERY
            # El .delay() envía el trabajo al worker y libera a Django
            procesar_csv_background.delay(validacion.id, nombre_usuario_str)

            messages.success(request, "✅ Archivo recibido. El proceso ha comenzado en segundo plano. Puedes seguir navegando.")
            return redirect('consultas:detalle_validacion', validacion.id)
    
    else:
        form = ArchivoCSVForm()
    return render(request, 'consultas/cargar_archivo.html', {'form': form})

@login_required
def ingresar_manual(request):
    if request.method == 'POST':
        form = DatosManualForm(request.POST)
        if form.is_valid():
            # 1. Crear el registro maestro de la validación
            usuario_instancia = request.user 
            nombre_usuario_str = request.user.get_username()
            validacion = ValidacionArchivo.objects.create(
                usuario=usuario_instancia,
                nombre_archivo=f"Manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 2. Configurar entorno del scraping
            config_scraping.set_headless_mode(True)
            set_service_url("http://localhost:5001")

            # 3. Verificar que el web service esté disponible ANTES de procesar
            import requests
            service_url = "http://localhost:5001"
            service_available = False
            try:
                response = requests.get(f"{service_url}/health", timeout=5)
                if response.status_code == 200:
                    service_available = True
                    print("✅ Web Service disponible")
                else:
                    print(f"⚠️ Web Service respondió con status {response.status_code}")
            except requests.exceptions.ConnectionError:
                print("❌ Web Service no disponible - Conexión fallida")
                service_available = False
            except Exception as e:
                print(f"❌ Error verificando Web Service: {e}")
                service_available = False

            # 4. Preparar datos
            person_data = {
                'NAME': form.cleaned_data['NAME'].upper().strip(),
                'LASTNAME': form.cleaned_data['LASTNAME'].upper().strip(),
                'ID': str(form.cleaned_data['ID']).strip(),
                'FECHA-EXP': form.cleaned_data['FECHA_EXP'].strftime('%Y-%m-%d') if form.cleaned_data.get('FECHA_EXP') else "",
                'TIPO': form.cleaned_data['tipo_documento'],
                'CITY': form.cleaned_data.get('ciudad', 'BOGOTA').upper(),
                'USER': nombre_usuario_str
            }

            # 5. Cargar flujos de la base de datos (solo una vez)
            tipo_doc = form.cleaned_data['tipo_documento']
            all_flows = database.load_flows_from_db(doc_type=tipo_doc)

            # 6. Variables para el resultado
            resultado_api = None
            error_mensaje = None
            estado = 'fallido'

            # 7. SOLO procesar si el web service está disponible
            if service_available:
                try:
                    print(f"🚀 Enviando solicitud a {service_url}/run_multi...")
                    resultado_api = process_person(person_data, all_flows, current_user=nombre_usuario_str)
                    
                    # Verificar si el resultado contiene error
                    if resultado_api and isinstance(resultado_api, dict):
                        if resultado_api.get('success') == False or resultado_api.get('error'):
                            error_mensaje = resultado_api.get('error', 'Error desconocido en el web service')
                            resultado_api = None
                            estado = 'fallido'
                            print(f"❌ Web Service devolvió error: {error_mensaje}")
                        else:
                            estado = 'exitoso'
                            print("✅ Consulta procesada exitosamente")
                    else:
                        error_mensaje = "No se recibió respuesta válida del web service"
                        estado = 'fallido'
                        print(f"❌ {error_mensaje}")
                        
                except requests.exceptions.Timeout:
                    error_mensaje = "Timeout - El web service tardó demasiado en responder"
                    estado = 'fallido'
                    print(f"❌ {error_mensaje}")
                except requests.exceptions.ConnectionError:
                    error_mensaje = "No se pudo conectar al web service - Verifica que esté corriendo"
                    estado = 'fallido'
                    print(f"❌ {error_mensaje}")
                except Exception as e:
                    error_mensaje = f"Error inesperado: {str(e)}"
                    estado = 'fallido'
                    print(f"❌ {error_mensaje}")
            else:
                error_mensaje = "Web Service no disponible. Por favor inicia el servicio primero: python web_service.py"
                estado = 'fallido'
                print(f"❌ {error_mensaje}")

            # 8. Guardar el registro individual
            RegistroValidacion.objects.create(
                validacion=validacion,
                nombre=person_data['NAME'],
                apellido=person_data['LASTNAME'],
                tipo_documento=person_data['TIPO'],
                numero_documento=person_data['ID'],
                ciudad=person_data['CITY'],
                estado=estado,
                mensaje_respuesta="Consulta procesada" if estado == 'exitoso' else error_mensaje,
                respuesta_json=resultado_api if resultado_api else {'error': error_mensaje}
            )

            # 9. Actualizar contadores generales
            validacion.total_registros = 1
            validacion.registros_exitosos = 1 if estado == 'exitoso' else 0
            validacion.registros_fallidos = 0 if estado == 'exitoso' else 1
            validacion.save()

            # 10. Mostrar mensaje al usuario
            if estado == 'exitoso':
                messages.success(request, "✅ Consulta procesada exitosamente. Los reportes están disponibles.")
            else:
                messages.error(request, f"❌ Error al procesar la consulta: {error_mensaje}")

            return redirect('consultas:detalle_validacion', validacion_id=validacion.id)

    else:
        form = DatosManualForm()

    return render(request, 'consultas/ingresar_manual_2.html', {'form': form})


@login_required
def descargar_reporte_protegido(request, file_path):
    # 1. Definir la ruta base donde el Agente Web guarda los reportes
    base_path_agente = "/Users/oskarh2/Documents/pgma/baloto/web-agent/webservice/reports/"
    
    # 2. Limpiar el path por si viene con prefijos duplicados
    if file_path.startswith('reports/'):
        file_path = file_path.replace('reports/', '', 1)

    # 3. Construir la ruta absoluta al archivo PDF
    absolute_path = os.path.join(base_path_agente, file_path)

    # Depuración: para ver en consola qué ruta está intentando abrir
    print(f"DEBUG: Buscando archivo en: {absolute_path}")

    # 4. Verificación de seguridad: solo el dueño de la carpeta puede ver el archivo
    # El file_path suele ser 'usuario@email.com/Carpeta_Persona/archivo.pdf'
    folder_user = file_path.split('/')[0]
    
    if request.user.get_username() != folder_user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para ver este reporte.")

    # 5. Servir el archivo si existe
    if os.path.exists(absolute_path):
        with open(absolute_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = f'inline; filename={os.path.basename(absolute_path)}'
            return response
    
    # Si llegamos aquí, el archivo físicamente no está en el disco
    raise Http404(f"Archivo no encontrado en el servidor: {absolute_path}")

@login_required
def lista_validaciones(request):
    """Lista de todas las validaciones del usuario"""
    validaciones = ValidacionArchivo.objects.filter(usuario=request.user)
    paginator = Paginator(validaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'consultas/lista_validaciones.html', {
        'page_obj': page_obj,
        'titulo': 'Mis Validaciones'
    })

@login_required
def detalle_validacion(request, validacion_id):
    """Detalle de una validación específica"""
    validacion = get_object_or_404(ValidacionArchivo, id=validacion_id, usuario=request.user)
    registros = validacion.registros.all()
    # Preparamos los registros con su ruta de PDF
    nombre_usuario = request.user.get_username()
    for registro in registros:

        # Formato: usuario/Nombre_Apellido_TIPO
        nom = registro.nombre.strip().replace(' ', '_')
        ape = registro.apellido.strip().replace(' ', '_')
        tipo = registro.tipo_documento.strip()
        # Formato: Nombre_Apellido_TIPO
        folder_name = f"{nom}_{ape}_{tipo}"
        # Construimos el nombre de la carpeta (debe ser igual a lo que hace main.py)
        file_name = f"{nom}_{ape}_results_only.pdf"
        
        # Ahora sí usamos nombre_usuario porque el WS ya lo habrá creado[cite: 6]
        registro.relative_pdf_path = os.path.join(nombre_usuario, folder_name, file_name)
    
    paginator = Paginator(registros, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'consultas/detalle_validacion.html', {
        'validacion': validacion,
        'page_obj': page_obj,
        'titulo': f'Detalle: {validacion.nombre_archivo}'
    })

@login_required
def detalle_registro(request, registro_id):
    """Detalle de un registro específico"""
    registro = get_object_or_404(RegistroValidacion, id=registro_id, validacion__usuario=request.user)
    
    return render(request, 'consultas/detalle_registro.html', {
        'registro': registro,
        'titulo': f'Detalle de Validación - {registro.nombre} {registro.apellido}'
    })