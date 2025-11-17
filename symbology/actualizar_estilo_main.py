# actualizar_estilo_main.py
import os
import shutil
import json
from stylx_utils import get_cims_from_stylx, actualizar_cims_en_stylx
from cim_parser import extraer_datos_hatch, build_geometric_marker_layer

# --- CONFIGURACIÓN GLOBAL ---

# Grosor de línea fijo (ej: 0.1, 0.2). Pon None para usar el original/2.
ANCHO_LINEA_PERSONALIZADO = 0.1  

# Multiplicador de separación.
# 1.0 = Misma densidad que el hatch (pero en diagonal se ve más denso).
# 1.414 = Densidad visual matemáticamente idéntica.
# 1.5 = Un poco más separado (como en la V8).
FACTOR_SEPARACION = 1.42
# ----------------------------

def main():
    print(f"[DEBUG] --- INICIANDO SCRIPT (V11) ---")
    print(f"[CONF] Ancho Línea: {ANCHO_LINEA_PERSONALIZADO}")
    print(f"[CONF] Factor Separación: {FACTOR_SEPARACION}")
    
    # Rutas
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    ruta_base, nombre_ext = os.path.splitext(style_path_original)
    style_path_copia = f"{ruta_base}_MODIFICADO_V11_FINAL{nombre_ext}"

    if not os.path.exists(style_path_original):
        print("¡ERROR! No existe el archivo.")
        return

    try:
        shutil.copy(style_path_original, style_path_copia)
        print(f"Copia creada: {style_path_copia}")
    except Exception as e:
        print(f"¡ERROR copiando!: {e}")
        return

    all_cims = get_cims_from_stylx(style_path_copia, verbose=False) 
    
    print(f"\n--- Procesando {len(all_cims)} Símbolos ---")
    
    cims_a_actualizar = {} 
    
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

        print(f"\n  -> {nombre_simbolo} (ID: {item_id})")
        
        hatch_index = 0 
        
        for capa in capas_originales:
            capa_tipo = capa.get('type')
            
            if capa_tipo == 'CIMHatchFill':
                datos_hatch = extraer_datos_hatch(capa)
                
                if datos_hatch['color'] and datos_hatch['separation'] is not None:
                    
                    # Offset para líneas dobles (mrc_)
                    offset_ratio = 0.0 if hatch_index == 0 else 0.5
                    
                    nueva_capa = build_geometric_marker_layer(
                        hatch_color=datos_hatch['color'],
                        separation=datos_hatch['separation'],
                        hatch_width=datos_hatch['width'],
                        offset_ratio=offset_ratio,
                        custom_width=ANCHO_LINEA_PERSONALIZADO,
                        separation_factor=FACTOR_SEPARACION # <-- Factor aplicado
                    )
                    nuevas_capas.append(nueva_capa)
                    simbolo_modificado = True
                    
                    print(f"    [OK] Hatch {hatch_index + 1} reemplazado.")
                    hatch_index += 1
                else:
                    nuevas_capas.append(capa) 
                    print("    [ERROR] Faltan datos en el hatch.")
            
            elif capa_tipo == 'CIMSolidFill':
                nuevas_capas.append(capa)
            else:
                nuevas_capas.append(capa)
        
        if simbolo_modificado:
            cim_data['symbolLayers'] = nuevas_capas
            cims_a_actualizar[item_id] = cim_data

    if cims_a_actualizar:
        print(f"\n--- Guardando {len(cims_a_actualizar)} cambios ---")
        try:
            actualizar_cims_en_stylx(style_path_copia, cims_a_actualizar)
            print("¡LISTO! Archivo V11 generado.")
        except Exception as e:
            print(f"Error guardando: {e}")

if __name__ == "__main__":
    main()