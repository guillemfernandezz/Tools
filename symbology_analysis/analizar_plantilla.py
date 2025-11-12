# analizar_plantilla.py
import os
import json
from stylx_utils import get_cims_from_stylx # Importamos tu función

def main():
    """
    Script de ANÁLISIS.
    Extrae el JSON de un símbolo "antes" (con hatch) y "después" (con SVG)
    para encontrar la plantilla de reemplazo correcta.
    """
    print("--- INICIANDO SCRIPT DE ANÁLISIS DE PLANTILLA ---")
    
    # --- CONFIGURACIÓN ---
    # 1. Ruta al estilo ORIGINAL (el que tiene los hatches)
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    
    # 2. Nombre del símbolo original que has copiado (ej. 'mc_Cagl')
    simbolo_original_nombre = "mc_Cagl"

    # 3. Ruta al NUEVO estilo que creaste manualmente con UN solo símbolo
    style_path_plantilla = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\plantilla_svg.stylx" # <-- ¡CAMBIA ESTO!
    
    # 4. Nombres de los archivos de salida
    json_original_output = "_original_hatch.json"
    json_plantilla_output = "_plantilla_svg.json"
    # ---------------------

    # --- 1. Analizar el Símbolo Original (Hatch) ---
    print(f"\nLeyendo archivo .stylx original: {style_path_original}")
    if not os.path.exists(style_path_original):
        print(f"¡ERROR! No se encuentra el .stylx original.")
        return

    all_cims_original = get_cims_from_stylx(style_path_original, verbose=False)
    
    simbolo_original_encontrado = None
    for item_id, item_info in all_cims_original.items():
        if item_info.get('name') == simbolo_original_nombre:
            simbolo_original_encontrado = item_info['cim_data']
            print(f"¡ÉXITO! Encontrado símbolo original: '{simbolo_original_nombre}' (ID: {item_id})")
            break
            
    if not simbolo_original_encontrado:
        print(f"¡ERROR! No se pudo encontrar el símbolo '{simbolo_original_nombre}' en el .stylx original.")
        return

    # Guardar el JSON original
    try:
        with open(json_original_output, 'w', encoding='utf-8') as f:
            json.dump(simbolo_original_encontrado, f, indent=2, ensure_ascii=False)
        print(f"-> JSON del símbolo original guardado en: {json_original_output}")
    except Exception as e:
        print(f"¡ERROR! No se pudo escribir el archivo JSON original: {e}")


    # --- 2. Analizar el Símbolo Plantilla (SVG) ---
    print(f"\nLeyendo archivo .stylx de plantilla: {style_path_plantilla}")
    if not os.path.exists(style_path_plantilla):
        print(f"¡ERROR! No se encuentra el .stylx de plantilla en esa ruta.")
        return

    all_cims_plantilla = get_cims_from_stylx(style_path_plantilla, verbose=False)
    
    if len(all_cims_plantilla) == 0:
        print("¡ERROR! El .stylx de plantilla no contiene ningún símbolo.")
        return
    if len(all_cims_plantilla) > 1:
        print(f"ADVERTENCIA: El .stylx de plantilla tiene {len(all_cims_plantilla)} símbolos. Se usará el primero que se encuentre.")

    # Tomar el primer símbolo que encuentre en el diccionario
    simbolo_plantilla_encontrado = next(iter(all_cims_plantilla.values()))['cim_data']
    nombre_plantilla = next(iter(all_cims_plantilla.values()))['name']
    
    print(f"¡ÉXITO! Encontrado símbolo de plantilla: '{nombre_plantilla}'")

    # Guardar el JSON de la plantilla
    try:
        with open(json_plantilla_output, 'w', encoding='utf-8') as f:
            json.dump(simbolo_plantilla_encontrado, f, indent=2, ensure_ascii=False)
        print(f"-> JSON del símbolo de plantilla guardado en: {json_plantilla_output}")
    except Exception as e:
        print(f"¡ERROR! No se pudo escribir el archivo JSON de plantilla: {e}")

    print("\n--- ANÁLISIS TERMINADO ---")
    print(f"Por favor, abre y compara los archivos '{json_original_output}' y '{json_plantilla_output}'.")

if __name__ == "__main__":
    main()