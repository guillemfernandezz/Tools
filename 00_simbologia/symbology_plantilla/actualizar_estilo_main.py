# actualizar_estilo_main.py
import os
import shutil
from stylx_utils import get_cims_from_stylx, actualizar_cims_en_stylx
from cim_parser import extraer_datos_hatch, extraer_parametros_plantilla, parse_svg_geometry, build_svg_geometry_marker

def leer_contenido_svg(svg_path):
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"¡Error leyendo archivo SVG!: {e}")
        return None

def main():
    print("[DEBUG] --- INICIANDO SCRIPT (V15 - PARSER GEOMETRÍA SVG) ---")
    
    # --- CONFIGURACIÓN ---
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    
    # Tu SVG
    svg_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\dades\geologia-territorial-50000-geologic\ICGC_Geologia1_U+007A.svg"
    
    # Tu Plantilla
    style_path_plantilla = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\test.stylx"
    nombre_simbolo_plantilla = "ant_rebaixats_visorl"
    
    ruta_base, nombre_ext = os.path.splitext(style_path_original)
    style_path_copia = f"{ruta_base}_plantilla_step54{nombre_ext}"
    # ---------------------

    # 1. Leer y Parsear SVG
    if not os.path.exists(svg_path):
        print(f"¡ERROR! No existe el SVG: {svg_path}")
        return
    svg_content = leer_contenido_svg(svg_path)
    if not svg_content: return

    # Convertimos el texto del SVG en coordenadas CIM reales
    svg_rings, svg_frame = parse_svg_geometry(svg_content)
    if not svg_rings:
        print("¡ERROR! No se pudieron extraer coordenadas del SVG.")
        return

    # 2. Robar Parámetros Plantilla
    if not os.path.exists(style_path_plantilla):
        print(f"¡ERROR! No existe la plantilla: {style_path_plantilla}")
        return
    params_plantilla = extraer_parametros_plantilla(style_path_plantilla, nombre_simbolo_plantilla)

    # 3. Copiar Estilo
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
                    offset_ratio = 0.0 if hatch_index == 0 else 0.5
                    
                    # CONSTRUCCIÓN
                    nueva_capa = build_svg_geometry_marker(
                        svg_rings=svg_rings,        # Coordenadas del SVG
                        svg_frame=svg_frame,        # Frame calculado
                        hatch_color=datos_hatch['color'],
                        template_params=params_plantilla,
                        offset_ratio=offset_ratio
                    )
                    
                    nuevas_capas.append(nueva_capa)
                    simbolo_modificado = True
                    print(f"    [OK] Hatch {hatch_index + 1} reemplazado.")
                    hatch_index += 1
                else:
                    nuevas_capas.append(capa) 
            
            elif capa_tipo == 'CIMSolidFill':
                nuevas_capas.append(capa) 
            else:
                nuevas_capas.append(capa) 
        
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