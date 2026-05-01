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
    """Vista para cargar archivo CSV"""
    if request.method == 'POST':
        form = ArchivoCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            
            # Crear registro de validación
            validacion = ValidacionArchivo.objects.create(
                usuario=request.user,
                nombre_archivo=archivo.name,
                archivo=archivo
            )
            
            # Procesar archivo CSV
            try:
                # Leer el archivo
                decoded_file = archivo.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                
                exitosos = 0
                fallidos = 0
                
                for row_num, row in enumerate(reader, start=1):
                    if not row or len(row) < 6:
                        fallidos += 1
                        continue
                    
                    # Extraer datos de la fila
                    # Formato: NAME,LASTNAME,TIPO,ID,FECHA-EXP,CITY
                    nombre = row[0].strip() if len(row) > 0 else ''
                    apellido = row[1].strip() if len(row) > 1 else ''
                    tipo_documento = row[2].strip() if len(row) > 2 else ''
                    numero_documento = row[3].strip() if len(row) > 3 else ''
                    fecha_exp = row[4].strip().strip('"') if len(row) > 4 else ''
                    ciudad = row[5].strip() if len(row) > 5 else ''
                    
                    # Validar datos mínimos
                    if not all([nombre, apellido, tipo_documento, numero_documento, ciudad]):
                        fallidos += 1
                        RegistroValidacion.objects.create(
                            validacion=validacion,
                            nombre=nombre or 'N/A',
                            apellido=apellido or 'N/A',
                            tipo_documento=tipo_documento or 'CC',
                            numero_documento=numero_documento or 'N/A',
                            ciudad=ciudad or 'N/A',
                            estado='fallido',
                            mensaje_respuesta='Datos incompletos en el archivo CSV'
                        )
                        continue
                    
                    # Preparar datos para web service
                    datos_ws = {
                        'nombre': nombre,
                        'apellido': apellido,
                        'tipo_documento': tipo_documento,
                        'numero_documento': numero_documento,
                        'ciudad': ciudad,
                    }
                    
                    # Agregar fecha si existe y es válida
                    if fecha_exp and fecha_exp != '""':
                        try:
                            # Intentar parsear fecha en diferentes formatos
                            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                                try:
                                    fecha_obj = datetime.strptime(fecha_exp, fmt)
                                    datos_ws['fecha_expedicion'] = fecha_obj.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                    
                    # Llamar al web service
                    resultado = WebServiceCliente.validar_persona(datos_ws)
                    
                    # Guardar registro
                    RegistroValidacion.objects.create(
                        validacion=validacion,
                        nombre=nombre,
                        apellido=apellido,
                        tipo_documento=tipo_documento,
                        numero_documento=numero_documento,
                        ciudad=ciudad,
                        estado='exitoso' if resultado['exitoso'] else 'fallido',
                        mensaje_respuesta=resultado['mensaje'],
                        respuesta_json=resultado['datos_respuesta']
                    )
                    
                    if resultado['exitoso']:
                        exitosos += 1
                    else:
                        fallidos += 1
                
                # Actualizar estadísticas de la validación
                validacion.total_registros = exitosos + fallidos
                validacion.registros_exitosos = exitosos
                validacion.registros_fallidos = fallidos
                validacion.save()
                
                messages.success(
                    request,
                    f'✅ Archivo procesado: {exitosos} exitosos, {fallidos} fallidos'
                )
                return redirect('consultas:detalle_validacion', validacion.id)
                
            except Exception as e:
                messages.error(request, f'❌ Error al procesar el archivo: {str(e)}')
                return redirect('consultas:cargar_archivo')
    else:
        form = ArchivoCSVForm()
    
    return render(request, 'consultas/cargar_archivo.html', {'form': form})

@login_required
def ingresar_manual(request):
    if request.method == 'POST':
        form = DatosManualForm(request.POST)
        if form.is_valid():
            # 1. Crear el registro maestro de la validación
            validacion = ValidacionArchivo.objects.create(
                usuario=request.user,
                nombre_archivo=f"Manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 2. Configurar entorno del scraping[cite: 5]
            config_scraping.set_headless_mode(True)
            set_service_url("http://localhost:5001")

            # 3. Cargar flujos de la base de datos
            tipo_doc = form.cleaned_data['tipo_documento']
            all_flows = database.load_flows_from_db(doc_type=tipo_doc)

            # 4. Preparar datos con llaves exactas para el Web Service[cite: 2]
            # Usamos guion medio en FECHA-EXP porque así lo requiere el agente
            fecha_val = form.cleaned_data.get('FECHA_EXP')
            person_data = {
                'NAME': form.cleaned_data['NAME'].upper().strip(),
                'LASTNAME': form.cleaned_data['LASTNAME'].upper().strip(),
                'ID': form.cleaned_data['ID'].strip(),
                'FECHA-EXP': fecha_val.strftime('%Y-%m-%d') if fecha_val else "",
                'TIPO': tipo_doc,
                'CITY': form.cleaned_data.get('ciudad', 'BOGOTA').upper()
            }

            # 5. Ejecutar proceso (Esto envía la lista 'persons' al Web Service)
            resultado_api = process_person(person_data, all_flows)

            # 6. Guardar el registro individual (Corrección del KeyError)[cite: 5]
            estado = 'exitoso' if resultado_api else 'fallido'
            RegistroValidacion.objects.create(
                validacion=validacion,
                nombre=person_data['NAME'],
                apellido=person_data['LASTNAME'],
                tipo_documento=person_data['TIPO'],
                numero_documento=person_data['ID'], # Usamos la llave 'ID' del diccionario
                ciudad=person_data['CITY'],
                estado=estado,
                mensaje_respuesta="Consulta procesada" if resultado_api else "Error en Web Service",
                respuesta_json=resultado_api
            )

            # Actualizar contadores generales
            validacion.total_registros = 1
            validacion.registros_exitosos = 1 if resultado_api else 0
            validacion.registros_fallidos = 0 if resultado_api else 1
            validacion.save()

            return redirect('consultas:detalle_validacion', validacion_id=validacion.id)
    else:
        form = DatosManualForm()

    return render(request, 'consultas/ingresar_manual_2.html', {'form': form})


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