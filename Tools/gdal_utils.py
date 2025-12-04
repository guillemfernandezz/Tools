import os
from osgeo import gdal, osr

gdal.DontUseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Nota: NO activamos UseExceptions() para evitar que falle con proyecciones raras.

def _obtener_crs_legible(ds):
    """Función interna para extraer el CRS de forma segura."""
    try:
        wkt = ds.GetProjection()
        if not wkt:
            return "Sin Referencia Espacial"
        
        srs = osr.SpatialReference(wkt)
        # Intentamos identificar el código EPSG
        if srs.AutoIdentifyEPSG() == 0:
            autoridad = srs.GetAuthorityName(None)
            codigo = srs.GetAuthorityCode(None)
            if autoridad and codigo:
                return f"{autoridad}:{codigo}"
        
        # Si falla, devolvemos el nombre descriptivo
        return srs.GetAttrValue("PROJCS") or "Sistema Desconocido"
    except:
        return "Error leyendo CRS"

def inspeccionar_carpeta(ruta_carpeta, extensiones_validas=None):
    """
    Busca archivos raster en una carpeta y subcarpetas.
    Es robusta ante errores de proyección.
    """
    lista_resultados = []
    ruta_carpeta = os.path.normpath(ruta_carpeta)

    print(f"🔍 Buscando en: {ruta_carpeta} ...") # Opcional: Descomentar si quieres ver progreso

    for raiz, _, archivos in os.walk(ruta_carpeta):
        for nombre_archivo in archivos:
            
            # Filtro opcional por extensión
            if extensiones_validas:
                _, ext = os.path.splitext(nombre_archivo)
                if ext.lower() not in extensiones_validas:
                    continue

            ruta_completa = os.path.join(raiz, nombre_archivo)
            
            # Intentamos abrir sin miedo a excepciones fatales
            ds = gdal.Open(ruta_completa)
            
            if ds is not None:
                # Si GDAL lo abre (aunque tenga warnings), extraemos info
                info_archivo = {
                    "Nombre": nombre_archivo,
                    "Ruta": ruta_completa,
                    "Formato (Driver)": ds.GetDriver().LongName,
                    "Ancho (X)": ds.RasterXSize,
                    "Alto (Y)": ds.RasterYSize,
                    "Bandas": ds.RasterCount,
                    "CRS": _obtener_crs_legible(ds)
                }
                lista_resultados.append(info_archivo)
                ds = None # Cerrar siempre
            
    return lista_resultados

def mostrar_informe(lista_datos):
    """Muestra los resultados bonitos en consola."""
    if not lista_datos:
        print("\n❌ No se encontraron archivos para mostrar.\n")
        return

    print(f"\n✅ Se han encontrado {len(lista_datos)} archivos geoespaciales:\n")
    for item in lista_datos:
        print(f"📄 {item['Nombre']}")
        print(f"   ├─ Formato: {item['Formato (Driver)']}")
        print(f"   ├─ Tamaño:  {item['Ancho (X)']} x {item['Alto (Y)']}")
        print(f"   ├─ Bandas:  {item['Bandas']}")
        print(f"   └─ CRS:     {item['CRS']}")
        print("-" * 40)

def convertir_a_cog(ruta_entrada, carpeta_destino):
    """
    Convierte a COG arreglando el problema de SRS.
    """
    try:
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            
        nombre_archivo = os.path.basename(ruta_entrada)
        nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
        nombre_cog = f"{nombre_sin_ext}_COG.tif"
        ruta_final = os.path.join(carpeta_destino, nombre_cog)
        
        print(f"⚙️ Procesando: {nombre_archivo}")
        
        mis_opciones = gdal.TranslateOptions(
            format="COG",
            outputSRS="EPSG:25831",
            creationOptions=[
                "COMPRESS=LZW",
                "PREDICTOR=2",
                "OVERVIEWS=IGNORE_EXISTING"
            ]
        )
        
        ds = gdal.Translate(ruta_final, ruta_entrada, options=mis_opciones)
        ds = None
        
        return ruta_final

    except Exception as e:
        print(f"❌ Error convirtiendo: {e}")
        return None

def analizar_cog(ruta_archivo):
    """
    Auditoría técnica profunda de un archivo COG.
    Incluye Bit Depth, Overviews y Tiling.
    """
    try:
        ds = gdal.Open(ruta_archivo)
        if not ds:
            return None

        # Metadatos básicos
        compresion = ds.GetMetadata('IMAGE_STRUCTURE').get('COMPRESSION', 'Desconocida')
        banda = ds.GetRasterBand(1)
        
        # --- BIT DEPTH ---
        tipo_dato_codigo = banda.DataType
        tipo_dato_texto = gdal.GetDataTypeName(tipo_dato_codigo)
        # -----------------

        num_overviews = banda.GetOverviewCount()
        bloque_x, bloque_y = banda.GetBlockSize()
        es_tiled = bloque_x != ds.RasterXSize
        
        info_tecnica = {
            "Archivo": os.path.basename(ruta_archivo),
            "Dimensiones Originales": f"{ds.RasterXSize} x {ds.RasterYSize}",
            "Tipo de Dato": tipo_dato_texto, # <--- Nuevo campo
            "Compresión": compresion,
            "Overviews": num_overviews,
            "Es Tiled": "✅ SÍ" if es_tiled else "❌ NO (Es Stripped)",
            "Tamaño Bloque": f"{bloque_x}x{bloque_y}",
            "Lista_Overviews": [] 
        }
        
        # Bucle de Overviews
        if num_overviews > 0:
            for i in range(num_overviews):
                ov = banda.GetOverview(i)
                desc_ov = {
                    "Nivel": i,
                    "Ancho": ov.XSize,
                    "Alto": ov.YSize
                }
                info_tecnica["Lista_Overviews"].append(desc_ov)
        
        ds = None
        return info_tecnica

    except Exception as e:
        print(f"Error analizando {ruta_archivo}: {e}")
        return None