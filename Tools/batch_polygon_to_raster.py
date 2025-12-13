import arcpy
import os
import time

aprx = arcpy.mp.ArcGISProject(r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\proyecto\tif_to_cogeotiff\tif_to_cogeotiff.aprx")
m = aprx.listMaps("Map")[0]

# Diccionario de elementos y sus acronimos:

acronimos = {
    "Alumini": "Al",
    "Argent": "Ag",
    "Arsènic": "As",
    "Berili": "Be",
    "Bismut": "Bi",
    "Bor": "B",
    "Bari": "Ba",
    "Cadmi": "Cd",
    "Calci": "Ca",
    "Ceri": "Ce",
    "Cesi": "Cs",
    "Coure": "Cu",
    "Crom": "Cr",
    "Escandi": "Sc",
    "Fòsfor": "P",
    "Lantani": "La",
    "Manganès": "Mn",
    "Molibdè": "Mo",
    "Neodimi": "Nd",
    "Niobi": "Nb",
    "Níquel": "Ni",
    "Or": "Au",
    "Plata": "Ag",
    "Plom": "Pb",
    "Potassi": "K",
    "Praseodimi": "Pr",
    "Sodi": "Na",
    "Zinc": "Zn"
}

print(f"--- Buscando capas poligonales en: {m.name}")

for lyr in m.listLayers():
    if lyr.isFeatureLayer:
        desc = arcpy.Describe(lyr)
        if desc.shapeType == "Polygon":
            print(f"\n✅ Candidato encontrado: {lyr.name}")
            print(f"    - ⚙️  Procesando {lyr.name}")
            
            # Para construir el nombre de salida:
            elemento = (lyr.name).split("_")[-1]
            key_elemento_mayuscula = elemento.strip().capitalize()
            acronimo = acronimos[key_elemento_mayuscula].lower()
            gdb_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\proyecto\tif_to_cogeotiff\tif_to_cogeotiff.gdb"
            out_name = f"{key_elemento_mayuscula}_raster"
            
            # Parámetros para el polygon_to_raster:
            in_feature = lyr
            value_field = "rang_concentració_" + f"{acronimo}"
            out_rasterdataset = os.path.join(gdb_path, out_name)
            cellsize = 10
            build_rat = True
            
            # --- ⏱️ INICIO DEL TEMPORIZADOR ---
            start_time = time.time()
                
            try:
                # Ejecución de la herramienta
                arcpy.PolygonToRaster_conversion(
                    in_features=in_feature, 
                    value_field=value_field, 
                    out_rasterdataset=out_rasterdataset, 
                    cellsize=cellsize,
                    build_rat="BUILD"
                )
                    
                # --- ⏱️ FIN DEL TEMPORIZADOR ---
                end_time = time.time()
                elapsed_time = end_time - start_time
                    
                # Imprimimos formateando a 2 decimales (.2f)
                print(f"        - ✅ Polígono procesado con éxito! [Tiempo: {elapsed_time:.2f} s]")
                
            except arcpy.ExecuteError:
                print(f"        - ❌ Error de Geoprocesamiento en {lyr.name}:")
                print(arcpy.GetMessages(2))
            except Exception as e:
                print(f"        - ❌ Error inesperado: {str(e)}")
                
        else:
            pass
    
    else:
        pass