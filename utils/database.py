"""
Módulo de conexión y operaciones con base de datos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Configuración de base de datos
DB_CONFIG = {
    'dbname': 'gestor_consultas',
    'user': 'oskarh2',
    'host': 'localhost',
    'password': ''
}

def set_db_config(dbname=None, user=None, host=None, password=None):
    """Update database configuration globally"""
    global DB_CONFIG
    if dbname:
        DB_CONFIG['dbname'] = dbname
    if user:
        DB_CONFIG['user'] = user
    if host:
        DB_CONFIG['host'] = host
    if password is not None:
        DB_CONFIG['password'] = password
    print(f"📁 Database config updated: {DB_CONFIG['dbname']}@{DB_CONFIG['host']} as {DB_CONFIG['user']}")


def get_db_config():
    """Get current database configuration"""
    return DB_CONFIG.copy()


# utils/database.py

# utils/database.py

def get_flows_from_db(doc_type=None):
    conn = None
    flows = {}
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            host=DB_CONFIG['host'],
            password=DB_CONFIG['password']
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # DEFINICIÓN DE LA VARIABLE (Crucial)
        val_buscar = str(doc_type).strip().upper() if doc_type else "CC"
        
        query = """
            SELECT page, type, steps 
            FROM page_tracking 
            WHERE TRIM(status::text) ILIKE 'COMPLETED' 
            AND TRIM(type::text) ILIKE %s;
        """
        
        # Ejecución usando la variable ya definida
        cur.execute(query, (val_buscar,))
        rows = cur.fetchall()
        
        print(f"\n🔍 DATABASE RESULT: Se encontraron {len(rows)} filas para '{val_buscar}'")

        for row in rows:
            # Creamos la llave: 'ofac_sanctions_CC'
            site_id = f"{str(row['page']).strip()}_{str(row['type']).strip().upper()}"
            
            steps_data = row['steps']
            if isinstance(steps_data, str):
                temp_data = json.loads(steps_data)
            else:
                temp_data = steps_data
            
            # Si el JSON viene envuelto en {"steps": [...]}, lo desempaquetamos aquí
            if isinstance(temp_data, dict) and 'steps' in temp_data:
                flows[site_id] = temp_data['steps']
            else:
                flows[site_id] = temp_data
            # Convertimos a dict si es necesario
            flows[site_id] = json.loads(steps_data) if isinstance(steps_data, str) else steps_data
            print(f"✅ Flujo registrado en memoria: {site_id}")

        return flows

    except Exception as e:
        print(f"❌ Error en DB: {e}")
        return {}
    finally:
        if conn: conn.close()

def load_flows_from_db(doc_type=None):
    """Wrapper for get_flows_from_db"""
    return get_flows_from_db(doc_type)