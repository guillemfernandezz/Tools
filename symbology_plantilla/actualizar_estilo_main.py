# actualizar_estilo_main.py
import os
import shutil
import base64
import json
import sqlite3
import re 
from stylx_utils import get_cims_from_stylx, actualizar_cims_en_stylx
from cim_parser import extraer_datos_hatch, extraer_parametros_plantilla, build_svg_marker_with_params

def convertir_svg_a_base64_y_limpiar(svg_path):
    print(f"[DEBUG] Procesando SVG: {svg_path}")
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        # Limpieza de estilos
        svg_content_cleaned = re.sub(r'\s(fill|stroke|style)=["\'][^"\']*["\']', '', svg_content)
        svg_bytes = svg_content_cleaned.encode('utf-8')
        base64_bytes = base64.b64encode(svg_bytes)
        return f"data:image/svg+xml;base64,{base64_bytes.decode('utf-8')}"
    except Exception as e:
        print(f"¡ERROR SVG!: {e}")
        return None

def main():
    print("[DEBUG] --- INICIANDO SCRIPT (V_FINAL_SVG_PLANTILLA) ---")
    
    # --- CONFIGURACIÓN ---
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    
    # Ruta al SVG
    svg_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\dades\geologia-territorial-50000-geologic\ICGC_Geologia1_U+007A.svg"
    
    # Ruta al Stylx de Plantilla
    style_path_plantilla = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\test.stylx"
    # Nombre del símbolo maestro en esa plantilla
    nombre_simbolo_plantilla = "ant_rebaixats_visor" # o "ant_rebaixats_visor"
    
    ruta_base, nombre_ext = os.path.splitext(style_path_original)
    style_path_copia = f"{ruta_base}_MODIFICADO_SVG_PLANTILLA{nombre_ext}"
    # ---------------------

    # 1. Cargar SVG
    svg_data_url = convertir_svg_a_base64_y_limpiar(svg_path)
    if not svg_data_url: return

    # 2. Robar Parámetros de la Plantilla
    params_plantilla = extraer_parametros_plantilla(style_path_plantilla, nombre_simbolo_plantilla)

    # 3. Preparar Copia
    if not os.path.exists(style_path_original):
        print("¡ERROR! No existe el original.")
        return
    try:
        shutil.copy(style_path_original, style_path_copia)
    except Exception as e:
        print(f"¡ERROR copiando!: {e}")
        return

    # 4. Procesar
    all_cims = get_cims_from_stylx(style_path_copia, verbose=False) 
    cims_a_actualizar = {} 
    
    print(f"\n--- Procesando {len(all_cims)} Símbolos ---")
    
    for item_id, item_info in all_cims.items():
        cim_data = item_info['cim_data']
        nombre_simbolo = item_info['name']
        simbolo_modificado = False

        if 'symbolLayers' not in cim_data: continue
        
        nuevas_capas = [] 
        capas_originales = cim_data.get('symbolLayers', [])
        
        contiene_hatch = any(capa.get('type') == 'CIMHatchFill' for capa in capas_originales)
        if not contiene_hatch: continue

        print(f"\n  -> {nombre_simbolo} (ID: {item_id})")
        hatch_index = 0 
        
        for capa in capas_originales:
            capa_tipo = capa.get('type')
            
            if capa_tipo == 'CIMHatchFill':
                datos_hatch = extraer_datos_hatch(capa)
                
                if datos_hatch['color']:
                    # Offset para mrc_
                    offset_ratio = 0.0 if hatch_index == 0 else 0.5
                    
                    nueva_capa = build_svg_marker_with_params(
                        svg_data_url=svg_data_url,
                        hatch_color=datos_hatch['color'],
                        template_params=params_plantilla, # Usamos los params robados
                        offset_ratio=offset_ratio
                    )
                    
                    nuevas_capas.append(nueva_capa)
                    simbolo_modificado = True
                    print(f"    [OK] Hatch {hatch_index + 1} reemplazado.")
                    hatch_index += 1
                else:
                    nuevas_capas.append(capa) 
            
            elif capa_tipo == 'CIMSolidFill':
                nuevas_capas.append(capa) # Conservar fondo
            else:
                nuevas_capas.append(capa) # Conservar otros
        
        if simbolo_modificado:
            cim_data['symbolLayers'] = nuevas_capas
            cims_a_actualizar[item_id] = cim_data

    # 5. Guardar
    if cims_a_actualizar:
        try:
            actualizar_cims_en_stylx(style_path_copia, cims_a_actualizar)
            print(f"\n¡LISTO! Archivo guardado: {style_path_copia}")
        except Exception as e:
            print(f"Error guardando: {e}")

if __name__ == "__main__":
    main()