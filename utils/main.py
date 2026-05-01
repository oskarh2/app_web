#!/usr/bin/env python3
"""
Programa Principal - Web Agent
Lee input.csv, consulta base de datos y llama al web service
"""

import pandas as pd
import json
import os
import sys
import argparse
import requests
from datetime import datetime
# Importar módulos locales
from database import set_db_config, load_flows_from_db, get_db_config
from scraping_config import set_headless_mode, get_headless_mode


# Configuración del servicio web (NO usar global dentro de funciones)
SERVICE_URL = "http://localhost:5001"


def set_service_url(url):
    """Actualizar URL del servicio web"""
    global SERVICE_URL
    SERVICE_URL = url
    print(f"📡 Web Service URL: {SERVICE_URL}")


def get_service_url():
    """Obtener URL del servicio web"""
    return SERVICE_URL


def check_service():
    """Verificar que el servicio web esté disponible"""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Web Service disponible")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al Web Service")
        print(f"   Asegúrate de que el servicio esté corriendo en {SERVICE_URL}")
        print("   Ejecuta: python web_service.py")
        return False
    return False


# utils/main.py

def process_person(person_data, all_flows, pdf_base_path="./reports"):
    """
    Procesar una persona consultando todos los flows
    Llama al web service para cada sitio
    """
    full_name = f"{person_data.get('NAME', '')} {person_data.get('LASTNAME', '')}".strip()
    doc_type = str(person_data.get('TIPO', '')).strip()
    
    print(f"\n{'='*60}")
    print(f"Procesando: {full_name}")
    print(f"Tipo documento: {doc_type}")
    print(f"{'='*60}")
    
    if not doc_type:
        print("  ⚠️ No TIPO encontrado, saltando...")
        return None
    
    # Obtener flows filtrados por tipo de documento
    flows_filtered = {}
    for site_id, flow_steps in all_flows.items():
        if site_id.endswith(f"_{doc_type}"):
            # --- NUEVA VALIDACIÓN CRÍTICA ---
            if isinstance(flow_steps, str):
                try:
                    import json
                    flow_steps = json.loads(flow_steps)
                except Exception as e:
                    print(f"  ❌ Error parseando JSON para {site_id}: {e}")
                    continue
            # -------------------------------
            flows_filtered[site_id] = flow_steps
    
    if not flows_filtered:
        print(f"  ⚠️ No flows encontrados para tipo: {doc_type}")
        return None
    
    print(f"  ✅ Procesando {len(flows_filtered)} fuentes")
    # ============================================================
    # DEBUG: Verificar los flows filtrados
    # ============================================================
    print(f"\n🔍 DEBUG: Flows filtrados para {doc_type}:")
    for site_id, flow_steps in flows_filtered.items():
        print(f"  📋 {site_id}")
        # Asegurarnos de que flow_steps sea tratado como lista para el conteo
        steps_list = flow_steps if isinstance(flow_steps, list) else [flow_steps]
        print(f"     Steps count: {len(steps_list)}")
        
        if steps_list and len(steps_list) > 0:
            first_step = steps_list[0]
            # Usar .get solo si el elemento interno es un diccionario
            action = first_step.get('action') if isinstance(first_step, dict) else 'N/A'
            print(f"     First action: {action}")
        else:
            print(f"     ⚠️ NO STEPS FOUND!")
    print(f"{'='*50}\n")
    # ============================================================
    # FIN DEBUG
    # ============================================================
    
    # Crear directorio de reportes para esta persona si no existe
    person_dir = os.path.join(pdf_base_path, f"{full_name.replace(' ', '_')}_{doc_type}")
    if not os.path.exists(person_dir):
        os.makedirs(person_dir)
    
    # Preparar datos para el web service
    payload = {
        "person_data": person_data,
        "flows": flows_filtered,
        "headless": get_headless_mode(),
        "pdf_base_path": person_dir
    }
    # ============================================================
    # DEBUG: Verificar payload antes de enviar (CORREGIDO)
    # ============================================================
    print(f"\n🔍 PAYLOAD being sent to web service:")
    print(f"  URL: {SERVICE_URL}/run_multi")
    print(f"  Person: {person_data.get('NAME')} {person_data.get('LASTNAME')}")
    print(f"  Total flows: {len(flows_filtered)}")
    
    # ============================================================
    # DEBUG: Verificar payload antes de enviar (NORMALIZADO)
    # ============================================================
    print(f"\n🔍 PAYLOAD being sent to web service:")
    print(f"  URL: {SERVICE_URL}/run_multi")
    
    # Asegurar que los flows tengan el formato de lista correcto antes de enviar
    for site_name, flow_steps in flows_filtered.items():
        # Si es un string (JSON), lo convertimos a objeto
        if isinstance(flow_steps, str):
            flow_steps = json.loads(flow_steps)
        
        # Si el flujo viene envuelto en una lista extra [[...]], lo sacamos
        if isinstance(flow_steps, list) and len(flow_steps) > 0 and isinstance(flow_steps[0], list):
            flow_steps = flow_steps[0]
            
        # Si es un solo diccionario, lo metemos en una lista
        steps_list = flow_steps if isinstance(flow_steps, list) else [flow_steps]
        
        # Actualizamos el diccionario filtrado con la lista limpia
        flows_filtered[site_name] = steps_list

        print(f"\n  📋 Flow: {site_name}")
        print(f"     Steps in payload: {len(steps_list)}")
        for i, step in enumerate(steps_list[:3]):
            if isinstance(step, dict):
                # Intentar obtener 'action' en minúscula o mayúscula
                action = step.get('action') or step.get('Action') or "No action key"
                print(f"       Step {i+1}: {action}")
    
    print(f"{'='*50}\n")
    print(f'payload: {payload}')

    # ============================================================
    # FIN DEBUG
    # ============================================================
    try:
        print(f"🚀 Enviando solicitud a {SERVICE_URL}/run_multi...")
        # Aumentamos el timeout a 300 segundos por si el scraping demora
        response = requests.post(f"{SERVICE_URL}/run_multi", json=payload, timeout=300)
        
        if response.status_code == 200:
            print(f"✅ Respuesta recibida del Web Service")
            return response.json() # Esto es lo que Django espera recibir
        else:
            print(f"❌ Error en Web Service: {response.status_code}")
            return {"error": f"Error {response.status_code}", "detail": response.text}
            
    except Exception as e:
        print(f"❌ Excepción al llamar al Web Service: {e}")
        return {"error": str(e)}
    


def process_individual_reports(db_config=None, headless=False):
    """
    Función principal para procesar todos los individuos
    """
    # Verificar servicio web
    if not check_service():
        print("\n❌ No se puede continuar sin el Web Service")
        print("Por favor, inicia el servicio primero:")
        print("  python web_service.py --port 5001")
        return
    
    # Configurar base de datos si se proporcionó
    if db_config:
        set_db_config(**db_config)
    
    # Verificar input.csv
    if not os.path.exists("input.csv"):
        print("❌ Error: input.csv no encontrado!")
        return
    
    # Leer input.csv
    inputs = pd.read_csv("input.csv")
    print(f"✅ Cargados {len(inputs)} registros de input.csv")
    
    # Obtener tipos de documento únicos
    doc_types = inputs['TIPO'].unique()
    print(f"📋 Tipos de documento encontrados: {list(doc_types)}")
    
    # Cargar flows para cada tipo de documento
    all_flows = {}
    for doc_type in doc_types:
        print(f"\n📥 Cargando flows para tipo: {doc_type}")
        flows = load_flows_from_db(doc_type)
        all_flows.update(flows)
    
    if not all_flows:
        print("❌ No se cargaron flows. Verifica la base de datos.")
        return
    
    print(f"\n✅ Total flows cargados: {len(all_flows)}")
    
    # Crear directorio base para reportes
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_reports_dir = f"./reports_{timestamp}"
    os.makedirs(base_reports_dir, exist_ok=True)
    
    # Procesar cada persona
    results_summary = []
    
    for idx, person in inputs.iterrows():
        print(f"\n{'#'*60}")
        print(f"Persona {idx + 1}/{len(inputs)}")
        print(f"{'#'*60}")
        
        current_person = person.to_dict()
        
        result = process_person(
            person_data=current_person,
            all_flows=all_flows,
            pdf_base_path=base_reports_dir
        )
        
        if result:
            results_summary.append({
                'person': f"{current_person.get('NAME', '')} {current_person.get('LASTNAME', '')}".strip(),
                'success': True,
                'details': result
            })
        else:
            results_summary.append({
                'person': f"{current_person.get('NAME', '')} {current_person.get('LASTNAME', '')}".strip(),
                'success': False
            })
    
    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    success_count = sum(1 for r in results_summary if r['success'])
    print(f"Procesados: {len(results_summary)} personas")
    print(f"Exitosos: {success_count}")
    print(f"Fallidos: {len(results_summary) - success_count}")
    print(f"\n📁 Reportes guardados en: {base_reports_dir}")
    
    return results_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Web Agent - Programa Principal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                                    # Usa configuración por defecto
  python main.py --dbname gestor_consultas          # Base de datos específica
  python main.py --headless true                    # Modo headless
  python main.py --service-url http://localhost:5002  # Servicio en otro puerto
        """
    )
    
    # Argumentos de base de datos
    parser.add_argument("--dbname", type=str, default="webagent", help="Nombre de la base de datos")
    parser.add_argument("--dbuser", type=str, default="oskarh2", help="Usuario de la base de datos")
    parser.add_argument("--dbhost", type=str, default="localhost", help="Host de la base de datos")
    parser.add_argument("--dbpassword", type=str, default="", help="Contraseña de la base de datos")
    
    # Argumentos de headless
    parser.add_argument("--headless", type=str, default="false", 
                       choices=["true", "false", "True", "False", "yes", "no"],
                       help="Modo headless del navegador")
    
    # Argumentos del servicio
    parser.add_argument("--service-url", type=str, default="http://localhost:5001",
                       help="URL del Web Service")
    
    args = parser.parse_args()
    
    # Configurar modo headless
    set_headless_mode(args.headless)
    
    # Configurar URL del servicio
    set_service_url(args.service_url)
    
    # Configurar base de datos
    db_config = {
        'dbname': args.dbname,
        'user': args.dbuser,
        'host': args.dbhost,
        'password': args.dbpassword
    }
    
    print(f"\n{'='*50}")
    print("🚀 Web Agent - Programa Principal")
    print(f"{'='*50}")
    print(f"📁 Base de datos: {args.dbname}@{args.dbhost}")
    print(f"🖥️ Headless: {get_headless_mode()}")
    print(f"📡 Web Service: {SERVICE_URL}")
    print(f"{'='*50}\n")
    
    # Ejecutar procesamiento
    process_individual_reports(db_config=db_config, headless=get_headless_mode())