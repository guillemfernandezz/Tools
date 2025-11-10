# 1_stylx_utils.py
import sqlite3                                                                                              # Para conectarse y leer la base de datos SQLite. Un .stylx es una base de datos de este tipo.
import json                                                                                                 # Para traducir texto en formato JSON a diccionarios y listas de Python. La info de CIM está en JSON.                                                   
import os                                                                                                   # Para verificar si el path que le metemos existe o no

def get_cims_from_stylx(style_path, verbose=True):                                                          # Función. Verbose=True para que imprima mensajes en consola de progreso. Sise pone False, no imprime nada.
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
    all_symbol_cims = {}                                                                                    # Diccionario vacío para guardar los CIMs encontrados. Al final se devuelve este diccionario y es con lo que se trabaja.
    
    if verbose:
        print(f"Leyendo base de datos de estilo: {style_path}")

    if not os.path.exists(style_path):                                                                      # Comprueba que el path exista
        if verbose:
            print(f"¡ERROR! No se encuentra el archivo en esta ruta.")
        return all_symbol_cims                                                                              # Si no existe, devuelve el diccionario vacío y la funcion termina aquí.                                                                    

    try:
        conn = sqlite3.connect(style_path)                                                                  # Conecta con la base de datos SQLite.
        conn.text_factory = str                                                                             # Le dice a la conexion que cuando lea texto lo trate como un str de Python. Asi evitamos problemas con caracteres raros, como Bytes.
        cursor = conn.cursor()                                                                              # Un cursor es un "puntero" o herramienta que se usa para ejecutar comandos (consultas) SQL y recibir resultados.

        cursor.execute("SELECT ID, NAME, CONTENT FROM ITEMS")                                               # Le decimos al cursor que ejecute esta consulta SQL. Le pedimos el ID, nombre y contenido (CIM en JSON) de la tabla ITEMS.
        rows = cursor.fetchall()                                                                            # fetchall() obtiene todas las filas resultantes de la consulta y las guarda en 'rows', que es una lista de tuplas.
        
        if verbose:
            print(f"Se encontraron {len(rows)} filas en total. Analizando...")

        decoder = json.JSONDecoder()                                                                        # Esta herramienta nos permite convertir texto JSON en diccionarios y listas de Python.

        for row in rows:
            item_id, name, cim_json_string = row                                                            # Cada row es una tupla con (ID, NAME, CONTENT). Aquí las desempaquetamos en variables separadas.
            
            if cim_json_string and '"type":"CIM' in cim_json_string and 'Symbol"' in cim_json_string:       # Primer filtro: Comprobamos que el contenido no esté vacio y que en el texto JSON "type":"CIM" aparezca.
                try:                                                                                        # La tabla ITEMS contiene todo tipo de ítems, no solo símbolos. Por eso hacemos este filtro previo.                                     
                    cim_data, _ = decoder.raw_decode(cim_json_string.strip())                               # Usamos el decoder para convertir el texto JSON en un diccionario/lista de Python. strip() elimina espacios en blanco al inicio y final.
                    """ 
                        - ¿Por qué raw_decode y no json.loads? json.loads exige que el string sea un JSON perfecto y nada más. raw_decode es más robusto: parsea el primer objeto JSON válido que encuentra y simplemente ignora si hay "basura" o texto extra después. 
                        Es más seguro para este caso.

                        - cim_data, _: raw_decode devuelve dos cosas: el objeto parseado (cim_data, que será un diccionario) y un número (el índice donde terminó de leer). Como no te importa ese número, lo asignas a _ (una convención en Python para "ignorar")
                        este valor").
                    """
                    all_symbol_cims[item_id] = {                                                            # Si el try funciona guardamos el CIM en el diccionario all_symbol_cims. La clave sera un ID ej: 123 y el valor sera otro diccionario con 'name' y 'cim_data'.
                        'name': name,
                        'cim_data': cim_data
                    }
                    if verbose:
                        print(f"  -> ¡ÉXITO! Símbolo parseado (ID: {item_id}): {name}")
                except json.JSONDecodeError as e:                                                           # JSONDecodeError se lanza si el texto JSON está mal formado y no se puede parsear.
                    if verbose:
                        print(f"  -> ERROR (ID: {item_id}): El JSON está mal formado: {e}")
        conn.close()                                                                                        # Cerramos la conexión a la base de datos.                               

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
    print("Por favor, ejecute 'analizar_estilo_main.py' para analizar un estilo.")