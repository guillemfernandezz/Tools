from osgeo import gdal
import csv
import os
import sys

# Subimos un nivel para encontrar 'Tools'
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_superior = os.path.dirname(carpeta_actual)
sys.path.append(carpeta_superior)

from Tools import gdal_utils
from Tools import table_utils

def embed_rat_with_gdal(tif_path, csv_path):
    """
    Incrusta una Tabla de Atributos Raster (RAT) nativa usando GDAL.
    Define explícitamente el uso de columnas para que QGIS detecte la leyenda.
    
    Args:
        tif_path (str): Ruta al archivo .tif existente.
        csv_path (str): Ruta al CSV con los datos (Value, Texto).
    """
    print(f"--- ☢️ INICIANDO EMBEBIDO GDAL (Nativo) para: {os.path.basename(tif_path)} ---")

    # 1. Validar existencia
    if not os.path.exists(tif_path) or not os.path.exists(csv_path):
        print("❌ ERROR: Faltan archivos de entrada.")
        return False

    # 2. Leer CSV en memoria
    data_map = {} # {Value: Texto}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Detectar índices (insensible a mayúsculas)
            try:
                # Buscamos 'value'
                idx_val = next(i for i, h in enumerate(headers) if 'value' in h.lower())
                # Buscamos 'rang', 'conc', o 'class' para el texto
                idx_txt = next(i for i, h in enumerate(headers) if any(x in h.lower() for x in ['rang', 'conc', 'class']))
            except StopIteration:
                print("❌ ERROR: No pude identificar columnas Value/Texto en el CSV.")
                return False

            for row in reader:
                if row:
                    try:
                        val = int(float(row[idx_val]))
                        txt = row[idx_txt]
                        data_map[val] = txt
                    except ValueError:
                        continue # Saltar filas invalidas
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return False

    # 3. Abrir TIF en modo UPDATE (Escritura)
    # gdal.GA_Update permite modificar el archivo in-situ
    ds = gdal.Open(tif_path, gdal.GA_Update)
    if not ds:
        print("❌ ERROR: No se pudo abrir el TIF con GDAL (¿Está abierto en QGIS/ArcGIS?).")
        return False

    band = ds.GetRasterBand(1)

    # 4. Crear la Tabla de Atributos (RAT) desde cero
    rat = gdal.RasterAttributeTable()

    # --- DEFINICIÓN DE COLUMNAS (LA CLAVE DEL ÉXITO) ---
    
    # Columna 0: Value (MinMax usage es típico para el pixel value)
    # GFT_Integer = Tipo Entero
    # GFU_MinMax = Usage (Generalmente se usa para el valor del pixel)
    rat.CreateColumn("Value", gdal.GFT_Integer, gdal.GFU_MinMax)
    
    # Columna 1: Class_Name (Texto)
    # GFT_String = Tipo Texto
    # GFU_Name = Usage NAME (¡ESTO ES LO QUE QGIS BUSCA!)
    rat.CreateColumn("Class_Name", gdal.GFT_String, gdal.GFU_Name)
    
    # Columna 2: Count (Opcional, pero QGIS suele esperarla)
    rat.CreateColumn("Count", gdal.GFT_Integer, gdal.GFU_PixelCount)

    # 5. Rellenar Filas
    # GDAL espera que las filas se creen primero
    # Vamos a rellenar basado en el ID máximo para cubrir el rango si es U4 (0-15)
    max_val = max(data_map.keys())
    rat.SetRowCount(max_val + 1) # +1 porque es base 0

    for val in range(max_val + 1):
        # Establecer valor de píxel (Columna 0)
        rat.SetValueAsInt(val, 0, val)
        
        # Establecer Texto (Columna 1)
        if val in data_map:
            rat.SetValueAsString(val, 1, data_map[val])
        else:
            rat.SetValueAsString(val, 1, "") # Vacío si no hay dato
            
        # Establecer Count (Columna 2) - Ponemos 0 dummy si no tenemos el dato a mano
        rat.SetValueAsInt(val, 2, 0) 

    # 6. Guardar cambios
    print("  > Escribiendo RAT en el encabezado del archivo...")
    band.SetDefaultRAT(rat)
    
    # IMPORTANTE: Forzar volcado a disco y cierre
    band.FlushCache()
    ds.FlushCache()
    band = None
    ds = None
    
    print("✅ ¡ÉXITO! Tabla incrustada nativamente con GDAL.")
    return True

def run_pixel_perfect_workflow(layer_name, output_folder):
    
    # 1. ArcPy: Generar COG y CSV
    print("--- FASE 1: ARCPY ---")
    cog_path = table_utils.export_to_cog_arcpy(layer_name, output_folder)    
    
    # (Asumimos que export_to_cog devuelve ruta y export_csv ya se ejecutó)
    csv_path = os.path.join(output_folder, f"{layer_name.replace(' ', '_')}.csv")
    
    # 2. ArcPy: Generar Estilo Visual (.qml)
    # Seguimos generando el QML porque define los COLORES, no los datos.
    table_utils.generate_qgis_style(layer_name, output_folder)
    
    # 3. GDAL: Inyectar Datos (La Solución Opción B)
    print("--- FASE 2: GDAL ---")
    # Es vital asegurarse de que ArcPy ha liberado el archivo
    del cog_path # Liberar referencia si existía
    
    # Llamamos al cirujano
    tif_final_path = os.path.join(output_folder, f"{layer_name.replace(' ', '_')}.tif")
    gdal_utils.embed_rat_with_gdal(tif_final_path, csv_path)

    print("🏁 PROCESO FINALIZADO. Abre QGIS y prueba.")