import os
import sys
import time

# Subimos un nivel para encontrar 'Tools'
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_superior = os.path.dirname(carpeta_actual)
sys.path.append(carpeta_superior)

from Tools import gdal_utils

# --- CONFIGURA TU CARPETA DE SALIDA DE ARCGIS ---
CARPETA_COGS = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\ArcGIS_COG" 


Analisis = []

for archivo in os.listdir(CARPETA_COGS):
    """
    Itera por cada archivo dentro de la carpeta de COGs que terminen en .tif, les aplica 
    la función analizar_cog, y añade el resultado del análisi a la lista Analisis -> [].
    """
    if archivo.endswith("tif"):
            print(f"⚙️  Procesando: {archivo}")
            ruta_completa = os.path.join(CARPETA_COGS, archivo)
            datos = gdal_utils.analizar_cog(ruta_completa)
            Analisis.append(datos)

print("\n" + "="*50)
print(f"📊 Informe de calidad generado: {len(Analisis)} archivos procesados")
print("="*50 + "\n")

for reporte in Analisis:
    
    for clave, valor in reporte.items():
        if clave == "Archivo":
            print(f"  📂 Archivo: {valor}")
        elif clave == "Lista_Overviews":
            print("   └─ Overviews:")
            
            if valor:
                total_items = len(valor)
                for i, ov in enumerate(valor):
                    es_ultimo = (i == total_items - 1)
                    simbolo = "└─" if es_ultimo else "├─"
                    print(f"       {simbolo} Nivel {ov['Nivel']}: {ov['Ancho']}x{ov['Alto']} px")
            else:
                print("       ⚠️ CRÍTICO: No tiene pirámides de zoom.")
            
        else:
            print(f"   ├─ {clave}: {valor}")
    
    print("-" * 40)