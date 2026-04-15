# consultas/services.py (crea este archivo)
import requests
import json
from django.conf import settings
from django.contrib import messages

class WebServiceCliente:
    """Cliente para consumir el web service de validación"""
    
    # Configura la URL de tu web service aquí
    # Cambia esta URL por la real de tu web service
    WS_URL = getattr(settings, 'VALIDACION_WS_URL', 'http://localhost:8000/api/validar')
    
    @classmethod
    def validar_persona(cls, datos):
        """
        Valida una persona a través del web service
        
        Args:
            datos (dict): Diccionario con los datos de la persona
                {
                    'nombre': str,
                    'apellido': str,
                    'tipo_documento': str,
                    'numero_documento': str,
                    'fecha_expedicion': str (opcional),
                    'ciudad': str
                }
        
        Returns:
            dict: Resultado de la validación
        """
        try:
            # Preparar los datos para enviar al web service
            payload = {
                'nombre': datos.get('nombre', '').upper().strip(),
                'apellido': datos.get('apellido', '').upper().strip(),
                'tipo_documento': datos.get('tipo_documento', ''),
                'numero_documento': datos.get('numero_documento', '').strip(),
                'ciudad': datos.get('ciudad', '').upper().strip(),
            }
            
            # Agregar fecha de expedición si existe
            if datos.get('fecha_expedicion'):
                payload['fecha_expedicion'] = datos['fecha_expedicion']
            
            # Realizar la petición al web service
            # Puedes usar GET o POST según lo requiera tu web service
            response = requests.post(
                cls.WS_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Verificar respuesta
            if response.status_code == 200:
                resultado = response.json()
                return {
                    'exitoso': resultado.get('valido', resultado.get('success', False)),
                    'mensaje': resultado.get('mensaje', resultado.get('message', 'Validación completada')),
                    'datos_respuesta': resultado
                }
            else:
                return {
                    'exitoso': False,
                    'mensaje': f'Error en el web service: Código {response.status_code}',
                    'datos_respuesta': None
                }
                
        except requests.exceptions.Timeout:
            return {
                'exitoso': False,
                'mensaje': 'Timeout: El web service no respondió a tiempo',
                'datos_respuesta': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'exitoso': False,
                'mensaje': 'Error de conexión: No se pudo conectar al web service',
                'datos_respuesta': None
            }
        except Exception as e:
            return {
                'exitoso': False,
                'mensaje': f'Error inesperado: {str(e)}',
                'datos_respuesta': None
            }