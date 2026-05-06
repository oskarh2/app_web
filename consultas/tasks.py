import csv
import io
import os
import sys
from celery import shared_task
from django.contrib.auth.models import User
from .models import ValidacionArchivo, RegistroValidacion

import csv
import io
import os
import sys
from celery import shared_task
from django.contrib.auth.models import User
from .models import ValidacionArchivo, RegistroValidacion

@shared_task(name="consultas.tasks.procesar_csv_background")
def procesar_csv_background(validacion_id, nombre_usuario_str):
    """
    Tarea de Celery para procesar el CSV en segundo plano.
    """
    # Agregamos la raíz del proyecto al path del sistema
    # Esto permite que Celery encuentre 'utils', 'main', etc.
    sys.path.append(os.getcwd()) 

    try:
        # --- IMPORTACIONES DINÁMICAS ---
        # Se importan aquí adentro para evitar errores de carga al iniciar el worker
        from utils import database
        import scraping_config as config_scraping
        from main import process_person, set_service_url

        # 1. Recuperar el registro maestro de la base de datos de Django
        validacion = ValidacionArchivo.objects.get(id=validacion_id)
        archivo = validacion.archivo 
        
        # 2. Configurar el entorno de scraping
        config_scraping.set_headless_mode(True)
        set_service_url("http://localhost:5001")
        
        # 3. Leer y procesar el contenido del archivo CSV
        contenido = archivo.read().decode('utf-8')
        io_string = io.StringIO(contenido)
        reader = csv.reader(io_string, delimiter=',')
        
        next(reader, None) # Omitir la fila de encabezado
        
        exitosos = 0
        fallidos = 0
        
        for row in reader:
            clean_row = [col.strip().replace('"', '') for col in row]
            if len(clean_row) < 4: 
                continue

            person_data = {
                'NAME': clean_row[0].upper(),
                'LASTNAME': clean_row[1].upper(),
                'TIPO': clean_row[2].upper() or 'CC',
                'ID': clean_row[3],
                'FECHA-EXP': clean_row[4] if len(clean_row) > 4 else "",
                'CITY': clean_row[5].upper() if len(clean_row) > 5 else "BOGOTA",
                'USER': nombre_usuario_str
            }

            # Cargar flujos lógicos desde la base de datos externa (utils/database.py)
            all_flows = database.load_flows_from_db(doc_type=person_data['TIPO'])
            
            # Ejecutar el motor de scraping (main.py)
            resultado_api = process_person(person_data, all_flows, current_user=nombre_usuario_str)
            
            # Guardar el resultado individual en Django
            RegistroValidacion.objects.create(
                validacion=validacion,
                nombre=person_data['NAME'],
                apellido=person_data['LASTNAME'],
                tipo_documento=person_data['TIPO'],
                numero_documento=person_data['ID'],
                ciudad=person_data['CITY'],
                estado='exitoso' if resultado_api else 'fallido',
                respuesta_json=resultado_api
            )
            
            if resultado_api: 
                exitosos += 1
            else: 
                fallidos += 1
        
        # 4. Actualizar el estado final del proceso por lotes
        validacion.total_registros = exitosos + fallidos
        validacion.registros_exitosos = exitosos
        validacion.registros_fallidos = fallidos
        validacion.save()
        
        return f"Proceso finalizado: {exitosos} exitosos"

    except Exception as e:
        return f"Error en tarea: {str(e)}"