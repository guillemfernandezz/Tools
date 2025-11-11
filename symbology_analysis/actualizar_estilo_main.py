# actualizar_estilo_main.py
import os
import shutil
import base64
import json
import sqlite3
from stylx_utils import get_cims_from_stylx, actualizar_cims_en_stylx
# Importamos las *únicas* dos funciones que hay ahora en cim_parser.py
from cim_parser import extraer_datos_de_hatch, build_svg_marker 

def convertir_svg_a_base64(svg_path):
    """
    Lee un archivo SVG y lo convierte a un string Base64 
    para incrustarlo en el JSON del CIM.
    """
    try:
        # Importante: Usar 'rb' (leer en modo binario) es más seguro
        with open(svg_path, 'rb') as f:
            svg_bytes = f.read()
        
        base64_bytes = base64.b64encode(svg_bytes)
        base64_string = base64_bytes.decode('utf-8')
        
        # El formato final que necesita el CIM
        return f"data:image/svg+xml;base64,{base64_string}"
        
    except FileNotFoundError:
        print(f"¡ERROR! No se encontró el archivo SVG en: {svg_path}")
        return None
    except Exception as e:
        print(f"¡ERROR! Ocurrió un error al leer el SVG: {e}")
        return None

def main():
    """
    Función principal que reemplaza Hatch por SVG.
    """
    # --- CONFIGURACIÓN ---
    # 1. Ruta al estilo ORIGINAL
    style_path_original = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    
    # 2. Ruta al archivo SVG que quieres usar como patrón
    svg_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\dades\geologia-territorial-50000-geologic\ICGC_Geologia1_U+007A.svg" # ¡¡RECUERDA CAMBIAR ESTO!!
    
    # 3. Tamaño (en puntos) que tendrá el SVG en el símbolo
    svg_size_pt = 18.0
    # ---------------------

    # --- PREPARACIÓN ---
    print(f"Accediendo al estilo: {style_path_original}")
    if not os.path.exists(style_path_original):
        print("¡ERROR! No se encuentra el .stylx original. Abortando.")
        return

    # 0. Crear una copia para no dañar el original
    print(f"Creando copia de seguridad del estilo...")
    ruta_base, nombre_ext = os.path.splitext(style_path_original)
    style_path_copia = f"{ruta_base}_MODIFICADO{nombre_ext}"
    
    try:
        shutil.copy(style_path_original, style_path_copia)
        print(f"Copia creada en: {style_path_copia}")
    except Exception as e:
        print(f"¡ERROR! No se pudo crear la copia. ¿Está el .stylx abierto en ArcGIS Pro? {e}")
        return

    # 1. Cargar el SVG y convertirlo a Base64
    print("Cargando y convirtiendo SVG a Base64...")
    svg_data_url = convertir_svg_a_base64(svg_path)
    if not svg_data_url:
        print("No se pudo procesar el SVG. Abortando.")
        return
    print("-> SVG cargado con éxito.")

    # 2. Cargar todos los símbolos del .stylx
    all_cims = get_cims_from_stylx(style_path_copia, verbose=False) 
    if not all_cims:
        print("No se cargaron símbolos del estilo.")
        return
    
    print(f"\n--- 🔄 Procesando {len(all_cims)} Símbolos ---")
    
    cims_a_actualizar = {} # {id: nuevo_cim_data}
    simbolos_modificados_nombres = []
    simbolos_con_error = []

    # 3. Iterar y modificar los símbolos en memoria
    for item_id, item_info in all_cims.items():
        cim_data = item_info['cim_data']
        nombre_simbolo = item_info['name']
        simbolo_modificado = False

        if 'symbolLayers' not in cim_data:
            continue
        
        nuevas_capas = [] 
        
        for capa in cim_data.get('symbolLayers', []):
            if capa.get('type') == 'CIMHatchFill':
                print(f"  -> Encontrado CIMHatchFill en: {nombre_simbolo} (ID: {item_id})")
                
                # a. Extraer sus propiedades
                datos_hatch = extraer_datos_de_hatch(capa)
                
                # --- LÓGICA DE CONTROL MEJORADA ---
                if datos_hatch['color'] and datos_hatch['separation'] is not None:
                    # ¡ÉXITO! Tenemos todo lo necesario
                    nueva_capa_marker = build_svg_marker(
                        color_obj=datos_hatch['color'],
                        svg_data_url=svg_data_url,
                        separacion=datos_hatch['separation'],
                        tamano_pt=svg_size_pt
                    )
                    nuevas_capas.append(nueva_capa_marker)
                    simbolo_modificado = True
                    print(f"     ...Reemplazado por CIMVectorMarker (Color y Separación {datos_hatch['separation']}pt conservados)")
                
                else:
                    # ¡ERROR! No se pudo extraer el color o la separación.
                    # Mantenemos la capa original para evitar el fill transparente.
                    nuevas_capas.append(capa) 
                    print(f"     ...¡ERROR! No se pudo extraer color/separación. Se mantiene el hatch original.")
                    if nombre_simbolo not in simbolos_con_error:
                        simbolos_con_error.append(nombre_simbolo)
            
            else:
                # No es un hatch, se mantiene la capa tal cual
                nuevas_capas.append(capa)
        
        if simbolo_modificado:
            cim_data['symbolLayers'] = nuevas_capas
            cims_a_actualizar[item_id] = cim_data
            simbolos_modificados_nombres.append(nombre_simbolo)

    # 4. Escribir todos los cambios en la BD (en lote)
    if not cims_a_actualizar:
        print("\n--- ✅ Proceso Terminado ---")
        print("No se encontraron símbolos con 'CIMHatchFill' que se pudieran modificar.")
    else:
        print(f"\n--- 💾 Escribiendo {len(cims_a_actualizar)} cambios en la BD ---")
        try:
            actualizar_cims_en_stylx(style_path_copia, cims_a_actualizar)
            print("\n--- ✅ ¡Proceso Terminado! ---")
            print(f"Se modificaron {len(simbolos_modificados_nombres)} símbolos en el archivo:")
            print(style_path_copia)
            print("\nSímbolos modificados:")
            for nombre in simbolos_modificados_nombres:
                print(f"  - {nombre}")

            if simbolos_con_error:
                print(f"\n--- ⚠️ Símbolos con errores ({len(simbolos_con_error)}) ---")
                print("Los siguientes símbolos tenían un 'CIMHatchFill' que no se pudo parsear y se omitió:")
                for nombre in simbolos_con_error:
                    print(f"  - {nombre}")

        except Exception as e:
            print(f"\n--- ❌ ¡ERROR FATAL AL ESCRIBIR! ---")
            print(f"Ocurrió un error al actualizar el .stylx: {e}")

if __name__ == "__main__":
    main()