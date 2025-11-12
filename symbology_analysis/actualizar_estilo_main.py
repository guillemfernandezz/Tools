# actualizar_estilo_main.py
import os
import shutil
import base64
import json
import sqlite3
import re 
from stylx_utils import get_cims_from_stylx, actualizar_cims_en_stylx
from cim_parser import extraer_datos_hatch, build_svg_marker_layer 

def main():
    print("[DEBUG] --- INICIANDO SCRIPT 'actualizar_estilo_main.py' (Versión Plantilla JSON) ---")
    # --- CONFIGURACIÓN ---
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    # ¡Ya no necesitamos la ruta del SVG!
    # ---------------------

    print(f"Accediendo al estilo: {style_path_original}")
    if not os.path.exists(style_path_original):
        print("¡ERROR! No se encuentra el .stylx original. Abortando.")
        return

    print(f"Creando copia de seguridad del estilo para V2_TEST...")
    ruta_base, nombre_ext = os.path.splitext(style_path_original)
    
    # --- ¡CAMBIO 1: NUEVO NOMBRE DE ARCHIVO! ---
    style_path_copia = f"{ruta_base}_MODIFICADO_V3_TEST{nombre_ext}"
    
    try:
        shutil.copy(style_path_original, style_path_copia)
        print(f"Copia creada en: {style_path_copia}")
    except Exception as e:
        print(f"¡ERROR! No se pudo crear la copia. ¿Está el .stylx abierto en ArcGIS Pro? {e}")
        return

    all_cims = get_cims_from_stylx(style_path_copia, verbose=False) 
    if not all_cims:
        print("No se cargaron símbolos del estilo.")
        return
    
    print(f"\n--- Procesando {len(all_cims)} Símbolos ---")
    
    cims_a_actualizar = {} 
    simbolos_modificados_nombres = []
    simbolos_con_error = []

    for item_id, item_info in all_cims.items():
        cim_data = item_info['cim_data']
        nombre_simbolo = item_info['name']
        simbolo_modificado = False

        if 'symbolLayers' not in cim_data:
            continue
        
        nuevas_capas = [] 
        capas_originales = cim_data.get('symbolLayers', [])
        
        contiene_hatch = any(capa.get('type') == 'CIMHatchFill' for capa in capas_originales)
        
        if not contiene_hatch:
            continue

        print(f"\n  -> Símbolo encontrado: {nombre_simbolo} (ID: {item_id})")
        
        for capa in capas_originales:
            capa_tipo = capa.get('type')
            
            if capa_tipo == 'CIMHatchFill':
                print("    [DEBUG] Encontrada capa CIMHatchFill.")
                datos_hatch = extraer_datos_hatch(capa)
                
                if datos_hatch['color'] and datos_hatch['separation'] is not None:
                    nueva_capa_svg = build_svg_marker_layer(
                        hatch_color=datos_hatch['color'],
                        separation=datos_hatch['separation'],
                        hatch_width=datos_hatch['width']
                    )
                    nuevas_capas.append(nueva_capa_svg)
                    simbolo_modificado = True
                    print(f"    [DEBUG] REEMPLAZO por CIMVectorMarker programado.")
                else:
                    nuevas_capas.append(capa) 
                    print(f"    [DEBUG] ¡ERROR! No se pudieron extraer datos. Se mantiene el hatch original.")
                    if nombre_simbolo not in simbolos_con_error:
                        simbolos_con_error.append(nombre_simbolo)
            
            elif capa_tipo == 'CIMSolidFill':
                print("    [DEBUG] Conservando capa CIMSolidFill (fondo).")
                nuevas_capas.append(capa)
            
            else:
                print(f"    [DEBUG] Conservando capa desconocida: {capa_tipo}")
                nuevas_capas.append(capa)
        
        if simbolo_modificado:
            cim_data['symbolLayers'] = nuevas_capas
            cims_a_actualizar[item_id] = cim_data
            if nombre_simbolo not in simbolos_modificados_nombres:
                simbolos_modificados_nombres.append(nombre_simbolo)

    if not cims_a_actualizar:
        print("\n--- Proceso Terminado ---")
        print("No se encontraron símbolos con 'CIMHatchFill' para modificar.")
    else:
        print(f"\n--- Escribiendo {len(cims_a_actualizar)} cambios en la BD ---")
        try:
            actualizar_cims_en_stylx(style_path_copia, cims_a_actualizar)
            print("\n--- ¡Proceso Terminado! ---")
            print(f"Se modificaron {len(simbolos_modificados_nombres)} símbolos en el archivo:")
            print(style_path_copia)
            print("\nSímbolos modificados:")
            for nombre in simbolos_modificados_nombres:
                print(f"  - {nombre}")

            if simbolos_con_error:
                print(f"\n--- Símbolos con errores ({len(simbolos_con_error)}) ---")
                print("Los siguientes símbolos tenían un 'CIMHatchFill' que no se pudo parsear y se omitió:")
                for nombre in simbolos_con_error:
                    print(f"  - {nombre}")

        except Exception as e:
            print(f"\n--- ¡ERROR FATAL AL ESCRIBIR! ---")
            print(f"Ocurrió un error al actualizar el .stylx: {e}")

if __name__ == "__main__":
    main()