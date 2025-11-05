# 1_stylx_utils.py
import sqlite3
import json
import os

def get_cims_from_stylx(style_path, verbose=True):
    """
    Lee un archivo .stylx de ArcGIS Pro y extrae todas las definiciones
    de símbolos CIM.

    Args:
        style_path (str): La ruta completa al archivo .stylx.
        verbose (bool): Si es True, imprime el progreso en la consola.

    Returns:
        dict: Un diccionario donde la clave es el ID del ítem en la BD
              y el valor es un diccionario con 'name' y 'cim_data'.
              Ej: {1: {'name': 'Mi Simbolo', 'cim_data': {...}}}
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

# Esta parte es una buena práctica.
# Significa que este código solo se ejecuta si corres este script directamente,
# no cuando es importado por otro script.
if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute '3_analizar_estilo_main.py' para analizar un estilo.")