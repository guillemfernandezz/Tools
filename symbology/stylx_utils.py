# 1_stylx_utils.py
import sqlite3
import json  # <-- ¡ASEGÚRATE DE QUE ESTÉ IMPORTADO!
import os

def get_cims_from_stylx(style_path, verbose=True):
    """
    Lee un archivo .stylx de ArcGIS Pro y extrae todas las definiciones
    de símbolos CIM.
    """
    all_symbol_cims = {}
    
    if verbose:
        print(f"Leyendo base de datos de estilo: {style_path}")

    if not os.path.exists(style_path):
        if verbose:
            print(f"¡ERROR! No se encuentra el archivo en esta ruta.")
        return all_symbol_cims

    try:
        conn = sqlite3.connect(style_path)
        conn.text_factory = str
        cursor = conn.cursor()

        cursor.execute("SELECT ID, NAME, CONTENT FROM ITEMS")
        rows = cursor.fetchall()
        
        if verbose:
            print(f"Se encontraron {len(rows)} filas en total. Analizando...")

        decoder = json.JSONDecoder()

        for row in rows:
            item_id, name, cim_json_string = row
            
            if cim_json_string and '"type":"CIM' in cim_json_string and 'Symbol"' in cim_json_string:
                try:
                    cim_data, _ = decoder.raw_decode(cim_json_string.strip())
                    all_symbol_cims[item_id] = {
                        'name': name,
                        'cim_data': cim_data
                    }
                    if verbose:
                        print(f"  -> ¡ÉXITO! Símbolo parseado (ID: {item_id}): {name}")
                except json.JSONDecodeError as e:
                    if verbose:
                        print(f"  -> ERROR (ID: {item_id}): El JSON está mal formado: {e}")
        conn.close()

    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

    if verbose:
        print("\n--- Resumen de Carga ---")
        print(f"Total de simbologías CIM cargadas: {len(all_symbol_cims)}")

    return all_symbol_cims

# --- FUNCIÓN MODIFICADA CON DEPURACIÓN ---
def actualizar_cims_en_stylx(style_path, cims_a_actualizar):
    """
    Actualiza símbolos en un archivo .stylx.
    ¡ESTA FUNCIÓN MODIFICA EL ARCHIVO!
    """
    print(f"\n[DEBUG] Iniciando 'actualizar_cims_en_stylx' para {len(cims_a_actualizar)} items.")
    conn = None
    try:
        conn = sqlite3.connect(style_path)
        cursor = conn.cursor()
        
        update_data = [] # Lista de tuplas para executemany
        
        for item_id, cim_data in cims_a_actualizar.items():
            # Convertir el diccionario de Python de nuevo a un string JSON
            json_string = json.dumps(cim_data, ensure_ascii=False)
            
            # --- DEBUG ---
            if item_id == 2: # Solo para el primer item (mc_Cagl)
                print(f"[DEBUG] JSON que se escribirá para ID {item_id} (primeros 500 caracteres):")
                print(json_string[:500] + "...")
            # --- FIN DEBUG ---

            update_data.append((json_string, item_id))

        print(f"[DEBUG] Preparando consulta 'executemany' para {len(update_data)} actualizaciones.")
        cursor.executemany("UPDATE ITEMS SET CONTENT = ? WHERE ID = ?", update_data)
        
        print("[DEBUG] Cambios enviados a la BD. Ejecutando 'commit'...")
        conn.commit()
        print("[DEBUG] 'Commit' exitoso.")
        
        if conn:
            conn.close()
            print("[DEBUG] Conexión a la BD cerrada.")
            
    except sqlite3.Error as e:
        print(f"[DEBUG] ¡Error de SQLite al actualizar!: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise
    except Exception as e:
        print(f"[DEBUG] ¡Error inesperado al actualizar!: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute 'analizar_estilo_main.py' para analizar un estilo.")