import os
import time
import unicodedata  # <--- IMPORTANTE: Para arreglar los caracteres raros
from osgeo import gdal, osr

gdal.DontUseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Nota: NO activamos UseExceptions() para evitar que falle con proyecciones raras.

# --- FUNCIONES AUXILIARES ---

def normalizar_texto(texto):
    """
    Convierte 'concentració' -> 'concentracio'.
    Elimina acentos y caracteres especiales para evitar errores en las cabeceras del TIFF.
    """
    if not isinstance(texto, str):
        return str(texto)
    
    # Normaliza unicode (NFD separa caracteres de sus tildes)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    # Filtra los caracteres que no son de combinación (las tildes)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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

# --- FUNCIONES DE INSPECCIÓN ---

def inspeccionar_carpeta(ruta_carpeta, extensiones_validas=None):
    """
    Busca archivos raster en una carpeta y subcarpetas.
    Es robusta ante errores de proyección.
    """
    lista_resultados = []
    ruta_carpeta = os.path.normpath(ruta_carpeta)

    print(f"🔍 Buscando en: {ruta_carpeta} ...") 

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
            "Tipo de Dato": tipo_dato_texto, 
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

# --- FUNCIONES DE CONVERSIÓN Y RAT ---

def convertir_a_cog(ruta_entrada, carpeta_destino):
    """
    Versión SIMPLE de conversión (sin tabla).
    Mantengo esta función porque estaba en tu archivo original.
    """
    try:
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            
        nombre_archivo = os.path.basename(ruta_entrada)
        nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
        nombre_cog = f"{nombre_sin_ext}_COG.tif"
        ruta_final = os.path.join(carpeta_destino, nombre_cog)
        
        print(f"⚙️ Procesando (Simple): {nombre_archivo}")
        
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

def generar_inyectar_rat(ds, diccionario_datos=None):
    """
    Calcula el histograma, crea la RAT básica (Value/Count) 
    e inyecta columnas extra si vienen en 'diccionario_datos'.
    INCLUYE LIMPIEZA DE CARACTERES (UTF-8).
    """
    banda = ds.GetRasterBand(1)
    
    # 1. Comprobación de Tipo (Solo Enteros)
    if banda.DataType > 5: 
        print("   ⚠️  AVISO: Raster Flotante. Se omite RAT.")
        return False

    print("   🔨 Generando Raster Attribute Table (RAT)...")

    # 2. Calcular Histograma
    try:
        banda.ComputeStatistics(0)
        min_val, max_val = banda.ComputeRasterMinMax(True)
        min_val, max_val = int(min_val), int(max_val)
        
        hist = banda.GetHistogram(min_val - 0.5, max_val + 0.5, max_val - min_val + 1, False, False)
    except Exception as e:
        print(f"   ❌ Error calculando histograma: {e}")
        return False

    # 3. Crear la Tabla (RAT)
    rat = gdal.RasterAttributeTable()
    rat.CreateColumn("Value", gdal.GFT_Integer, gdal.GFU_MinMax)
    rat.CreateColumn("Count", gdal.GFT_Integer, gdal.GFU_PixelCount)
    
    # --- CREAR COLUMNAS EXTRA (CON LIMPIEZA DE TEXTO) ---
    columnas_extra_mapa = [] # Lista de tuplas (nombre_original, nombre_limpio)
    
    if diccionario_datos and len(diccionario_datos) > 0:
        try:
            # Cogemos las llaves del primer elemento
            primer_val = next(iter(diccionario_datos.values()))
            raw_keys = list(primer_val.keys())
            
            for raw_key in raw_keys:
                # 1. Limpiamos el nombre de la cabecera (rang_concentració -> rang_concentracio)
                col_name_clean = normalizar_texto(raw_key)
                
                # 2. Creamos columna
                rat.CreateColumn(col_name_clean, gdal.GFT_String, gdal.GFU_Generic)
                
                # 3. Guardamos la relación para luego buscar los datos
                columnas_extra_mapa.append((raw_key, col_name_clean))
                
        except StopIteration:
            pass 
    # ---------------------------------------------------

    # 4. Rellenar la tabla
    row_index = 0
    valores_inyectados = 0
    
    for i, count in enumerate(hist):
        if count > 0:
            pixel_value = int(min_val + i)
            
            rat.SetValueAsInt(row_index, 0, pixel_value) # Col 0: Value
            rat.SetValueAsInt(row_index, 1, int(count))  # Col 1: Count
            
            # --- RELLENAR DATOS EXTRA ---
            if diccionario_datos and pixel_value in diccionario_datos:
                info_extra = diccionario_datos[pixel_value] # { 'Campo': 'Valor', ... }
                
                # Iteramos sobre las columnas mapeadas
                for j, (raw_key, _) in enumerate(columnas_extra_mapa):
                    
                    # Obtenemos el valor usando la clave ORIGINAL (con acentos)
                    valor_original = str(info_extra.get(raw_key, ""))
                    
                    # Escribimos en la columna correspondiente (Offset de 2)
                    idx_columna = 2 + j 
                    rat.SetValueAsString(row_index, idx_columna, valor_original)
            # ---------------------------
            
            row_index += 1
            valores_inyectados += 1

    # 5. Guardar en el dataset
    err = banda.SetDefaultRAT(rat)
    if err != 0:
        print("   ❌ Error crítico seteando la RAT.")
        return False

    print(f"   ✅ RAT inyectada correctamente. Filas: {valores_inyectados}. Atributos extra: {len(columnas_extra_mapa)}")
    return True

def verificar_rat(ruta_archivo):
    """Abre el archivo y confirma que la tabla existe."""
    ds = gdal.Open(ruta_archivo, gdal.GA_ReadOnly)
    if not ds: return False
    
    banda = ds.GetRasterBand(1)
    rat = banda.GetDefaultRAT()
    
    if rat is None:
        ds = None
        return False
    
    cols = rat.GetColumnCount()
    rows = rat.GetRowCount()
    print(f"   🕵️  DEBUG: Tabla final -> Columnas: {cols}, Filas: {rows}")
    ds = None
    return (cols > 0 and rows > 0)

def convertir_a_cog_con_tabla(ruta_entrada, carpeta_destino, inyectar_tabla=True, diccionario_datos=None):
    """
    Función Maestra AVANZADA:
    1. Convierte a COG (PREDICTOR=1).
    2. Espera desbloqueo de Windows.
    3. Abre con OpenEx (IGNORE_COG_LAYOUT_BREAK) e inyecta tabla + atributos.
    """
    if not os.path.exists(carpeta_destino):
        try: os.makedirs(carpeta_destino)
        except: pass
            
    nombre_archivo = os.path.basename(ruta_entrada)
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    nombre_cog = f"{nombre_sin_ext}_COG.tif"
    ruta_final = os.path.join(carpeta_destino, nombre_cog)
    
    print(f"\n⚙️  PROCESANDO: {nombre_archivo}")

    # 1. Configuración GDAL
    opciones_cog = gdal.TranslateOptions(
        format="COG",
        outputSRS="EPSG:25831", 
        creationOptions=[
            "COMPRESS=LZW",
            "PREDICTOR=1",  # Vital para compatibilidad con GDBs
            "OVERVIEWS=IGNORE_EXISTING",
            "STATISTICS=YES"
        ]
    )
    
    # 2. Conversión
    ds_cog = gdal.Translate(ruta_final, ruta_entrada, options=opciones_cog)
    
    if ds_cog is None:
        print(f"❌ Error CRÍTICO en gdal.Translate: {gdal.GetLastErrorMsg()}")
        return None
    
    ds_cog = None # Cerrar para guardar en disco
    
    # 3. Pausa Táctica (File Locking)
    time.sleep(1.0) 
    
    # 4. Inyección
    if inyectar_tabla:
        print("   🔄 Reabriendo para inyección de tabla y atributos...")
        
        # Usamos OpenEx para permitir editar el COG
        ds_update = gdal.OpenEx(
            ruta_final,
            gdal.OF_RASTER | gdal.OF_UPDATE, 
            open_options=["IGNORE_COG_LAYOUT_BREAK=YES"]
        )
        
        if ds_update:
            # Pasamos el diccionario aquí
            exito_rat = generar_inyectar_rat(ds_update, diccionario_datos=diccionario_datos)
            ds_update = None 
            
            if exito_rat:
                if verificar_rat(ruta_final):
                    print("   ✨ ÉXITO TOTAL: COG creado y Tabla completa.")
                else:
                    print("   ⚠️  ALERTA: Falló la verificación de la tabla.")
            else:
                print("   ⚠️  No se generó la tabla.")
        else:
            print(f"   ❌ Error reabriendo archivo: {gdal.GetLastErrorMsg()}")

    return ruta_final

def procesar_todo_a_cog(carpeta_origen, carpeta_destino):
    """
    Función maestra para CARPETAS (No GDBs): Recorre, convierte e inyecta tabla básica.
    """
    archivos = inspeccionar_carpeta(carpeta_origen, extensiones_validas=['.tif', '.tiff', '.img'])
    
    if not archivos:
        print("No se encontraron rasters para procesar.")
        return

    print(f"\n🚀 Iniciando procesamiento por lotes de {len(archivos)} archivos...\n")
    
    errores = 0
    exitos = 0
    
    for item in archivos:
        # Aquí no pasamos diccionario_datos porque en una carpeta suelta no solemos tenerlo a mano
        resultado = convertir_a_cog_con_tabla(item['Ruta'], carpeta_destino, inyectar_tabla=True)
        if resultado:
            exitos += 1
        else:
            errores += 1
            
    print("\n" + "="*50)
    print(f"RESUMEN FINAL: Éxitos: {exitos} | Fallos: {errores}")
    print("="*50 + "\n")