from osgeo import gdal, osr
import os

gdal.PushErrorHandler('CPLQuietErrorHandler')

def obtener_crs(ds):
    wkt = ds.GetProjection()
    if not wkt:
        return "Sin Referencia Espacial"
    
    srs = osr.SpatialReference(wkt)
    # Intentamos leer el código oficial (ej: EPSG 25831)
    if srs.AutoIdentifyEPSG() == 0: # 0 significa éxito en GDAL
        autoridad = srs.GetAuthorityName(None)
        codigo = srs.GetAuthorityCode(None)
        if autoridad and codigo:
            return f"{autoridad}:{codigo}"
    
    # Si no tiene código EPSG, devolvemos el nombre (ej: ETRS89 / UTM zone 31N)
    return srs.GetAttrValue("PROJCS") or "Sistema Desconocido"

def get_tiff_info(path):
    
    lista_resultados = []
    nombre_carpeta = path.split("\\")[-1]
    
    print(f"\nBuscando archivos en: \\{nombre_carpeta} ...")
    
    for raiz, directorios, archivos in os.walk(path):
        for nombre_archivo in archivos:
            
            ruta_completa = os.path.join(raiz, nombre_archivo)
            
            ds = gdal.Open(ruta_completa)
            
            if ds is not None:
                crs_legible = obtener_crs(ds)
                
                info_archivo = {
                    "Nombre" : nombre_archivo,
                    "Ruta" : ruta_completa,
                    "Formato (Driver)": ds.GetDriver().LongName,
                    "Ancho (X)": ds.RasterXSize,
                    "Alto (Y)": ds.RasterYSize,
                    "Bandas": ds.RasterCount,
                    "CRS": crs_legible
                }
                
                lista_resultados.append(info_archivo)

                ds = None
                
            else:
                pass
    
    return lista_resultados

path = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\ArcGIS_COG"

informe = get_tiff_info(path)

# Mostramos los resultados bonitos
print(f"\n Se han encontrado {len(informe)} archivos geoespaciales:\n")
for item in informe:
    print(f"📄 {item['Nombre']}")
    print(f"   ├─ Formato: {item['Formato (Driver)']}")
    print(f"   ├─ Tamaño:  {item['Ancho (X)']} x {item['Alto (Y)']}")
    print(f"   ├─ Bandas:  {item['Bandas']}")
    print(f"   └─ CRS:  {item['CRS']}")
    print("-" * 40)