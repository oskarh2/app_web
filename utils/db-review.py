import psycopg2
import json

conn = psycopg2.connect(
    dbname="gestor_consultas",
    user="oskarh2",
    host="localhost",
    password=""
)

cur = conn.cursor()
cur.execute("SELECT page, type, steps FROM page_tracking WHERE status = 'COMPLETED'")
rows = cur.fetchall()

for row in rows:
    print(f"\n{'='*50}")
    print(f"Page: {row[0]}, Type: {row[1]}")
    steps = row[2]
    print(f"Type of steps: {type(steps)}")
    print(f"Steps content: {steps}")
    
    if isinstance(steps, str):
        try:
            parsed = json.loads(steps)
            print(f"Parsed JSON type: {type(parsed)}")
            if isinstance(parsed, dict):
                print(f"Keys in dict: {parsed.keys()}")
                if 'steps' in parsed:
                    print(f"Steps inside: {len(parsed['steps'])} steps")
                else:
                    print(f"Dict content: {parsed}")
            elif isinstance(parsed, list):
                print(f"List length: {len(parsed)}")
                for i, item in enumerate(parsed[:3]):
                    print(f"  Item {i}: {item}")
        except Exception as e:
            print(f"Error parsing: {e}")
    else:
        print(f"Steps is not string: {steps}")

cur.close()
conn.close()