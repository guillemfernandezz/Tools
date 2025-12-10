import os
import sys
import time

# --- IMPORTACIÓN DE LIBRERÍA "TOOLS" ---
# Subimos un nivel para encontrar la carpeta 'Tools'
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_superior = os.path.dirname(carpeta_actual)
sys.path.append(carpeta_superior)

from Tools import gdal_utils

# --- RUTAS DE TRABAJO ---
CARPETA_ORIGEN = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\output_tif"
CARPETA_DESTINO = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\ArcGIS_COG"
NOMBRE_INFORME = "informe_calidad_cogs.txt"

def generar_informe_txt(carpeta_cogs):
    """
    Genera un informe TXT detallado con la auditoría de calidad.
    """
    ruta_informe = os.path.join(carpeta_cogs, NOMBRE_INFORME)
    print(f"\n📝 Escribiendo informe técnico en: {NOMBRE_INFORME} ...")
    
    archivos = [f for f in os.listdir(carpeta_cogs) if f.endswith(".tif")]
    
    with open(ruta_informe, "w", encoding="utf-8") as f:
        # Cabecera
        f.write("=" * 60 + "\n")
        f.write(f"  AUDITORÍA TÉCNICA COG (Cloud Optimized GeoTIFF)\n")
        f.write(f"  Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Archivos procesados: {len(archivos)}\n")
        f.write("=" * 60 + "\n\n")

        for archivo in archivos:
            ruta_completa = os.path.join(carpeta_cogs, archivo)
            datos = gdal_utils.analizar_cog(ruta_completa)
            
            if datos:
                f.write("-" * 40 + "\n")
                f.write(f"📁 Archivo:      {datos['Archivo']}\n")
                f.write(f"📏 Dimensiones:   {datos['Dimensiones Originales']}\n")
                f.write(f"💾 Tipo Dato:     {datos['Tipo de Dato']} (Bit Depth)\n") # <--- NUEVO
                f.write(f"🗜️  Compresión:    {datos['Compresión']}\n")
                f.write(f"🧱 Tiling:        {datos['Es Tiled']} ({datos['Tamaño Bloque']})\n")
                f.write(f"🔺 Overviews:     {datos['Overviews']}\n")
                
                if datos['Lista_Overviews']:
                    for ov in datos['Lista_Overviews']:
                        # Cálculo porcentaje reducción
                        ancho_orig = int(datos['Dimensiones Originales'].split(' x ')[0])
                        pct = (ov['Ancho'] / ancho_orig) * 100 if ancho_orig > 0 else 0
                        f.write(f"    └─ Nivel {ov['Nivel']}: {ov['Ancho']}x{ov['Alto']} px (~{pct:.1f}%)\n")
                else:
                    f.write("    ⚠️ CRÍTICO: No tiene pirámides de zoom.\n")
                
                f.write("\n")

    print(f"✅ Informe guardado con éxito.")

def ejecutar_procesamiento_masivo():
    print("=" * 60)
    print(f"🏭  INICIANDO FACTORÍA DE COGs")
    print(f"   📂 Origen:  {CARPETA_ORIGEN}")
    print(f"   📂 Destino: {CARPETA_DESTINO}")
    print("=" * 60 + "\n")

    # 1. ESCANEAR
    print("🔍 Buscando mapas originales...")
    lista_mapas = gdal_utils.inspeccionar_carpeta(CARPETA_ORIGEN, extensiones_validas=['.tif', '.tiff'])
    
    total = len(lista_mapas)
    if total == 0:
        print("❌ No hay mapas .tif en la carpeta origen.")
        return

    print(f"📋 Encontrados {total} mapas.\n")
    
    # 2. PROCESAR
    if not os.path.exists(CARPETA_DESTINO):
        os.makedirs(CARPETA_DESTINO)

    exitos = 0
    errores = 0
    inicio = time.time()

    for i, mapa in enumerate(lista_mapas, 1):
        ruta_tif = mapa['Ruta']
        nombre = mapa['Nombre']
        
        print(f"[{i}/{total}] 🚀 Procesando: {nombre}...")
        
        resultado = gdal_utils.convertir_a_cog(ruta_tif, CARPETA_DESTINO)
        
        if resultado:
            exitos += 1
        else:
            errores += 1
            print(f"      ❌ ERROR con {nombre}")

    tiempo_total = time.time() - inicio

    # 3. RESUMEN
    print("\n" + "=" * 60)
    print(f"🏁 PROCESO FINALIZADO EN {tiempo_total:.2f} SEGUNDOS")
    print(f"✅ Éxitos: {exitos} | ❌ Errores: {errores}")
    print("=" * 60)

    # 4. INFORME FINAL
    if exitos > 0:
        generar_informe_txt(CARPETA_DESTINO)

if __name__ == "__main__":
    ejecutar_procesamiento_masivo()