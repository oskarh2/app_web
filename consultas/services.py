# consultas/services.py (crea este archivo)
import requests
import json
import os
from django.conf import settings

class WebServiceCliente:
    @staticmethod
    def validar_persona(datos):
        """
        Llama al endpoint del Agente Web (Flask)
        """
        url = 'http://localhost:5001/run_with_links_file'
        
        # Ruta al archivo JSON de pasos (ajusta según tu estructura)
        links_file_path = os.path.join(settings.BASE_DIR, 'config', 'xx.json')
        
        # Mapeo de campos para el Agente Web
        person_data = {
            "NAME": datos.get('nombre', ''),
            "LASTNAME": datos.get('apellido', ''),
            "ID": datos.get('numero_documento', '')
        }

        try:
            with open(links_file_path, 'rb') as f:
                files = {'links_file': f}
                data = {
                    'person_data': json.dumps(person_data),
                    'headless': 'true',
                    'pdf_base_path': './media/reports' # Carpeta donde Flask guardará
                }
                
                response = requests.post(url, data=data, files=files, timeout=120)
                
                if response.status_code == 200:
                    res_json = response.json()
                    return {
                        'exitoso': True,
                        'mensaje': 'Consulta completada exitosamente',
                        'datos_respuesta': res_json,
                        'pdf_path': res_json.get('pdf_path')
                    }
                else:
                    return {
                        'exitoso': False, 
                        'mensaje': f'Error en servidor de automatización: {response.status_code}',
                        'datos_respuesta': None
                    }
        except Exception as e:
            return {
                'exitoso': False,
                'mensaje': f'Error de conexión: {str(e)}',
                'datos_respuesta': None
            }