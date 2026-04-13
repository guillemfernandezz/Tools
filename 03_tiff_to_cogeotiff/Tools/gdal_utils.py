# -*- coding: utf-8 -*-
import os
import time
import unicodedata
import arcpy  # Integramos ArcPy aquí para la lectura
from osgeo import gdal, osr, gdalconst

# Configuración de GDAL para entornos de producción
gdal.DontUseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

# --- 1. UTILIDADES DE TEXTO (Conservadas) ---

def normalizar_texto(texto):
    """
    Limpia strings para cabeceras de metadatos.
    Convierte 'concentració' -> 'concentracio' y elimina caracteres ilegales.
    """
    if texto is None: return ""
    if not isinstance(texto, str): return str(texto)
    
    # Normalización NFD para separar tildes
    nfkd_form = unicodedata.normalize('NFKD', texto)
    # Filtrar y volver a unir
    texto_limpio = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Reemplazar espacios por guiones bajos para compatibilidad XML/DBF
    return texto_limpio.replace(" ", "_").replace("-", "_")

# --- 2. EL PUENTE ARCPY -> PYTHON (Nueva) ---

def extraer_atributos_arcpy(layer_objeto):
    """
    Lee la tabla de atributos de una capa Raster de ArcGIS y la convierte
    en un diccionario Python optimizado para GDAL.
    Versión: DEBUGGING AGRESIVO.
    """
    print(f"   📊 Extrayendo atributos de: {layer_objeto.name}...")
    
    # 1. VERIFICACIÓN ROBUSTA DE RAT
    try:
        desc = arcpy.Describe(layer_objeto)
        if not desc.hasRAT:
            print("      ⚠️ AVISO: ArcPy dice que esta capa no tiene Tabla (hasRAT=False).")
            # Intento desesperado: Si es un Layer de mapa, a veces hasRAT miente.
            # Seguimos un poco más por si acaso.
    except Exception as e:
        print(f"      ⚠️ Error describiendo la capa (se intentará leer igual): {e}")

    diccionario_salida = {}
    
    # 2. DETECCIÓN DE CAMPOS
    try:
        # Listamos todos los campos
        todos_campos = arcpy.ListFields(layer_objeto)
        nombres_campos = [f.name for f in todos_campos]
        print(f"      🔎 Campos detectados: {nombres_campos}")
        
        # Filtramos los útiles (Ignoramos OID y Count para la carga, pero necesitamos Value)
        campos_a_leer = [f.name for f in todos_campos if f.type != 'OID']
    except Exception as e:
        print(f"      ❌ Error listando campos: {e}")
        return None

    # 3. CAZA DEL TESORO: BUSCAR EL CAMPO 'VALUE'
    # El campo puede llamarse: 'Value', 'VALUE', 'Pixel Value', 'UniqueValue.Pixel Value', etc.
    campo_valor = None
    
    posibles_nombres = ['Value', 'VALUE', 'Pixel Value', 'UniqueValue.Pixel Value']
    
    # Estrategia A: Búsqueda exacta
    for posible in posibles_nombres:
        if posible in nombres_campos:
            campo_valor = posible
            break
            
    # Estrategia B: Búsqueda por tipo (Primer entero que no sea OID ni Count)
    if not campo_valor:
        print("      ⚠️ No se encontró campo 'Value' estándar. Buscando primer entero candidato...")
        for f in todos_campos:
            if f.type in ['Integer', 'SmallInteger'] and f.name.upper() not in ['OBJECTID', 'OID', 'FID', 'COUNT']:
                campo_valor = f.name
                break
    
    if not campo_valor:
        print(f"      ❌ ERROR CRÍTICO: No se pudo identificar el campo ID del pixel en: {nombres_campos}")
        return None

    print(f"      🎯 Campo Clave identificado: '{campo_valor}'")

    # 4. LECTURA DE DATOS
    try:
        # Aseguramos que el campo valor esté en la lista de lectura
        if campo_valor not in campos_a_leer:
            campos_a_leer.append(campo_valor)
            
        print(f"      📖 Leyendo columnas: {campos_a_leer}")
        
        count_filas = 0
        with arcpy.da.SearchCursor(layer_objeto, campos_a_leer) as cursor:
            for row in cursor:
                info_fila = dict(zip(campos_a_leer, row))
                
                # Extraemos el ID del pixel
                pixel_id = info_fila.get(campo_valor)
                
                # Limpiamos el diccionario para no duplicar el ID dentro de los atributos
                # (Opcional: lo dejamos si quieres verlo en el popup también)
                
                if pixel_id is not None:
                    # Convertimos a int por seguridad
                    diccionario_salida[int(pixel_id)] = info_fila
                    count_filas += 1
                    
        print(f"      ✅ ÉXITO: Se leyeron {count_filas} registros de la tabla.")
        return diccionario_salida
        
    except Exception as e:
        print(f"      ❌ Error leyendo filas con ArcPy: {e}")
        import traceback
        traceback.print_exc() # Esto imprimirá el error real completo
        return None

# --- 3. CORE: CONVERSIÓN Y RAT (Optimizada) ---

def generar_xml_pam(ds, diccionario_datos):
    """
    Crea la RAT y fuerza a GDAL a escribirla.
    Si el TIF es COG (Read-Only), GDAL escribirá automáticamente el .aux.xml (PAM).
    """
    if not diccionario_datos:
        return False

    banda = ds.GetRasterBand(1)
    
    # Crear RAT GDAL
    rat = gdal.RasterAttributeTable()
    rat.CreateColumn("Value", gdalconst.GFT_Integer, gdalconst.GFU_MinMax)
    rat.CreateColumn("Count", gdalconst.GFT_Integer, gdalconst.GFU_PixelCount)

    # Definir columnas dinámicas basadas en el primer registro del diccionario
    primer_id = next(iter(diccionario_datos))
    columnas_origen = list(diccionario_datos[primer_id].keys())
    
    col_map = [] # [(nombre_origen, indice_destino), ...]
    
    for nombre_col in columnas_origen:
        nombre_clean = normalizar_texto(nombre_col)
        rat.CreateColumn(nombre_clean, gdalconst.GFT_String, gdalconst.GFU_Generic)
        # El índice es: 0=Value, 1=Count, 2...N=Extras. 
        # Como acabamos de crearla, su índice es GetColumnCount-1
        col_map.append((nombre_col, rat.GetColumnCount() - 1))

    # Rellenar filas
    # OJO: GDAL RAT funciona por índices de fila (0, 1, 2...), no por Valor de Pixel directo.
    # Necesitamos saber el rango de valores del raster para mapearlos.
    # Para simplificar y hacerlo robusto, crearemos una RAT "Sparse" o mapeada al histograma.
    
    # Estrategia Segura: Iteramos el diccionario y creamos filas.
    # Nota: Esto asume que el diccionario tiene todos los valores relevantes.
    rat.SetRowCount(len(diccionario_datos))
    
    row_idx = 0
    for pixel_val, atributos in diccionario_datos.items():
        rat.SetValueAsInt(row_idx, 0, int(pixel_val))
        # Count lo dejamos a 0 o calculamos si es crítico, pero para visualización no es vital.
        
        for nombre_orig, col_idx in col_map:
            valor = str(atributos.get(nombre_orig, ""))
            rat.SetValueAsString(row_idx, col_idx, valor)
            
        row_idx += 1

    # Inyección final
    print("      🔨 Escribiendo metadatos (esto generará el .aux.xml)...")
    err = banda.SetDefaultRAT(rat)
    
    if err == 0:
        return True
    else:
        print("      ⚠️ GDAL devolvió error al setear RAT (comprobar permisos).")
        return False

def procesar_capa_raster(layer_arcpy, carpeta_destino):
    """
    Orquestador principal para una capa.
    1. Lee atributos de ArcPy.
    2. Exporta temporalmente a TIFF (para que GDAL pueda leerlo fuera de la GDB).
    3. Convierte el Raster a COG.
    4. Inyecta la RAT (generando PAM).
    5. Limpia temporales.
    """
    nombre_capa = layer_arcpy.name
    
    # Normalizamos nombre para evitar problemas con espacios en archivos
    nombre_seguro = normalizar_texto(nombre_capa)
    
    print(f"\n🚀 Procesando capa: {nombre_capa}")
    
    # 1. Extraer Datos (si existen) usando la GDB original
    dict_atributos = extraer_atributos_arcpy(layer_arcpy)
    
    # --- PASO DE SEGURIDAD: EXPORTAR A TEMP ---
    # GDAL a veces no puede leer directamente dentro de una .gdb.
    # Usamos ArcPy para sacar el raster a una carpeta temporal segura.
    folder_temp = os.path.join(carpeta_destino, "TEMP_Processing")
    if not os.path.exists(folder_temp):
        os.makedirs(folder_temp)
        
    ruta_tif_temp = os.path.join(folder_temp, f"{nombre_seguro}_temp.tif")
    
    print(f"      📦 Exportando temporalmente desde GDB a TIF...")
    try:
        # Usamos CopyRaster de ArcPy, que es infalible para sacar cosas de una GDB
        arcpy.management.CopyRaster(
            in_raster=layer_arcpy,
            out_rasterdataset=ruta_tif_temp,
            pixel_type="", # Dejar que detecte automático
            format="TIFF"
        )
    except Exception as e:
        print(f"      ❌ Error exportando temporal: {e}")
        return False
    # ------------------------------------------
    
    # 2. Configurar Salida Final
    ruta_cog = os.path.join(carpeta_destino, f"{nombre_seguro}_COG.tif")
    
    # 3. Conversión a COG usando GDAL
    print(f"      ⚙️  Convirtiendo a COG (LZW) desde: {ruta_tif_temp}")
    
    # --- DIAGNÓSTICO PREVIO ---
    if not os.path.exists(ruta_tif_temp):
        print("      ❌ ERROR CRÍTICO: El archivo temporal no existe. ArcPy falló silenciosamente.")
        return False
        
    # Validar si GDAL puede leer el temporal antes de convertir
    ds_test = gdal.Open(ruta_tif_temp)
    if not ds_test:
        print(f"      ❌ ERROR: GDAL no puede abrir el archivo temporal. Razón: {gdal.GetLastErrorMsg()}")
        return False
    else:
        print(f"         (Check: GDAL puede leer el temporal. Driver: {ds_test.GetDriver().ShortName})")
        ds_test = None # Cerramos test
    # ---------------------------

    opciones = gdal.TranslateOptions(
        format="COG",
        outputSRS="EPSG:25831", 
        creationOptions=[
            "COMPRESS=LZW", 
            "PREDICTOR=1", 
            "OVERVIEWS=IGNORE_EXISTING"
        ]
    )
    
    # Limpiamos errores previos
    gdal.ErrorReset()
    
    ds = gdal.Translate(ruta_cog, ruta_tif_temp, options=opciones)
    
    if not ds:
        # AQUÍ ESTÁ LA CLAVE: Imprimimos el error real
        error_msg = gdal.GetLastErrorMsg()
        print(f"      ❌ Falló la conversión a COG.")
        print(f"      🕵️  DETALLE DEL ERROR GDAL: {error_msg}")
        
        # Limpieza de emergencia
        if os.path.exists(ruta_tif_temp):
            try: os.remove(ruta_tif_temp)
            except: pass
        return False
        
    ds = None # Cerrar COG
    
    # 4. Inyección de RAT (Estrategia PAM)
    if dict_atributos:
        print("      ⏳ Esperando desbloqueo de archivo (2s)...")
        time.sleep(2.0) # <--- LA CLAVE: Damos tiempo a Windows para soltar el archivo
        
        # Abrimos el COG final usando OpenEx y la opción para ignorar el bloqueo COG.
        # Al escribir una RAT compleja, GDAL derivará al .aux.xml sin romper el binario TIF.
        print("      🔓 Abriendo con permiso especial (IGNORE_COG_LAYOUT_BREAK)...")
        ds_pam = gdal.OpenEx(
            ruta_cog,
            gdal.OF_RASTER | gdal.OF_UPDATE,
            open_options=["IGNORE_COG_LAYOUT_BREAK=YES"]
        )
        
        if ds_pam:
            exito = generar_xml_pam(ds_pam, dict_atributos)
            ds_pam = None # Al cerrar aquí, se escribe el .aux.xml
            if exito:
                print("      ✅ Proceso completado: COG + PAM (.aux.xml)")
            else:
                print("      ⚠️  Se abrió el archivo, pero falló la escritura interna de la RAT.")
        else:
            # Ahora sabremos POR QUÉ falla si sigue fallando
            err_msg = gdal.GetLastErrorMsg()
            print(f"      ⚠️  COG creado, pero no se pudo reabrir para escribir metadatos.")
            print(f"      🕵️  Razón GDAL: {err_msg}")
    else:
        print("      ✅ Proceso completado: COG (Sin atributos extra)")

    # 5. Limpieza Final
    try:
        # Borramos el tif temporal y su xml asociado si existe
        if os.path.exists(ruta_tif_temp):
            os.remove(ruta_tif_temp)
        if os.path.exists(ruta_tif_temp + ".aux.xml"):
            os.remove(ruta_tif_temp + ".aux.xml")
        if os.path.exists(ruta_tif_temp + ".ovr"):
            os.remove(ruta_tif_temp + ".ovr")
        # Borramos la carpeta temp si está vacía
        try: os.rmdir(folder_temp)
        except: pass
    except:
        print("      ⚠️  No se pudieron borrar algunos archivos temporales.")
            
    return True

# --- 4. VALIDACIÓN (Conservada) ---

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