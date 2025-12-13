import arcpy
import os
import sys
import time
import shutil

# --- IMPORTACIÓN DE LIBRERÍA "TOOLS" ---
# Subimos un nivel para encontrar la carpeta 'Tools'
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_superior = os.path.dirname(carpeta_actual)
sys.path.append(carpeta_superior)

from Tools import gdal_utils

def procesar_rasters_de_mapa(ruta_aprx, nombre_mapa, carpeta_destino):
    
    # 1. Abrir Proyecto
    if not os.path.exists(ruta_aprx):
        print(f"❌ Error: No se encuentra el proyecto: {ruta_aprx}")
        return

    print(f"📂 Abriendo proyecto: {ruta_aprx}...")
    try:
        aprx = arcpy.mp.ArcGISProject(ruta_aprx)
        # Buscar mapa (insensible a mayúsculas)
        mapa_objetivo = None
        for m in aprx.listMaps():
            if m.name.lower() == nombre_mapa.lower():
                mapa_objetivo = m
                break
        
        if not mapa_objetivo:
            print(f"❌ Error: No se encontró el mapa '{nombre_mapa}'.")
            return
            
    except Exception as e:
        print(f"❌ Error abriendo proyecto: {e}")
        return

    print(f"🗺️  Mapa '{mapa_objetivo.name}' cargado. Escaneando capas...")
    
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Carpeta temporal
    carpeta_temp = os.path.join(carpeta_destino, "TEMP_EXPORT")
    if not os.path.exists(carpeta_temp):
        os.makedirs(carpeta_temp)

    conteo = 0

    # 2. Iterar Capas
    for capa in mapa_objetivo.listLayers():
        if capa.isRasterLayer:
            print("-" * 60)
            print(f"🔎 Analizando capa: '{capa.name}'")
            
            try:
                # --- A. LECTURA DE ATRIBUTOS (NUEVO) ---
                diccionario_atributos = {}
                try:
                    # Campos a ignorar porque se generan solos
                    ignorar = ['OID', 'Value', 'Count', 'Object_ID', 'Pixel Value', 'Rowid']
                    campos = [f.name for f in arcpy.ListFields(capa) if f.name not in ignorar]
                    
                    if campos:
                        print(f"   📥 Leyendo atributos originales: {campos}...")
                        # El primer campo del cursor DEBE ser el valor del pixel para usarlo de clave
                        with arcpy.da.SearchCursor(capa, ['Value'] + campos) as cursor:
                            for row in cursor:
                                val_pixel = int(row[0]) # Clave
                                # Diccionario: { 'NombreCampo': 'Valor', ... }
                                datos_fila = dict(zip(campos, row[1:]))
                                diccionario_atributos[val_pixel] = datos_fila
                        print(f"   📖 Atributos memorizados para {len(diccionario_atributos)} valores.")
                    else:
                        print("   ℹ️  La capa no tiene atributos extra (solo Value/Count).")
                        
                except Exception as e_att:
                    print(f"   ⚠️  No se pudo leer la tabla de atributos (quizás es flotante): {e_att}")
                
                # --- B. PREPARAR RUTA FÍSICA ---
                conn_props = capa.connectionProperties
                if not conn_props: continue
                
                workspace = conn_props.get('connection_info', {}).get('database', '')
                dataset = conn_props.get('dataset', '')
                
                ruta_gdal = ""
                es_temp = False

                # Si es GDB -> Exportar a Temp
                if workspace.endswith('.gdb'):
                    print("   📦 Origen Geodatabase -> Exportando temporal...")
                    ruta_temp = os.path.join(carpeta_temp, f"{capa.name}.tif")
                    
                    if arcpy.Exists(ruta_temp):
                        arcpy.management.Delete(ruta_temp)
                    
                    arcpy.management.CopyRaster(capa, ruta_temp, pixel_type=None, format="TIFF")
                    
                    print("   ⏳ Esperando liberación de archivo...")
                    time.sleep(2.0) # Pausa importante
                    
                    ruta_gdal = ruta_temp
                    es_temp = True
                else:
                    # Archivo físico directo
                    posible_ruta = os.path.join(workspace, dataset)
                    if os.path.exists(posible_ruta):
                        ruta_gdal = posible_ruta
                    elif os.path.exists(capa.dataSource):
                        ruta_gdal = capa.dataSource

                # --- C. LLAMADA A TU LIBRERÍA ---
                if ruta_gdal and os.path.exists(ruta_gdal):
                    
                    # Llamamos a la función pasando el diccionario de atributos
                    res = gdal_utils.convertir_a_cog_con_tabla(
                        ruta_entrada=ruta_gdal,
                        carpeta_destino=carpeta_destino,
                        inyectar_tabla=True,
                        diccionario_datos=diccionario_atributos # <--- AQUÍ PASAMOS LOS DATOS
                    )
                    
                    if res: conteo += 1
                else:
                    print("   ❌ No se encontró el archivo físico.")

                # Limpieza Temp de este archivo
                if es_temp:
                    try: 
                        if os.path.exists(ruta_gdal): os.remove(ruta_gdal)
                    except: pass

            except Exception as e:
                print(f"❌ Error procesando capa '{capa.name}': {e}")

    # Limpieza final carpeta
    try: shutil.rmtree(carpeta_temp)
    except: pass

    print(f"\n✅ FIN DEL PROCESO. Rasters convertidos: {conteo}")

if __name__ == "__main__":
    # --- CONFIGURACIÓN ---
    PROYECTO = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\proyecto\tif_to_cogeotiff\tif_to_cogeotiff.aprx"
    MAPA = "Map"
    SALIDA = r"C:\Users\becari.g.fernandez\Desktop\test_output_final"

    procesar_rasters_de_mapa(PROYECTO, MAPA, SALIDA)