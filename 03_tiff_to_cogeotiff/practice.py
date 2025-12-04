import sys
import os
import time

carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_arriba = os.path.dirname(carpeta_actual) 
sys.path.append(carpeta_arriba)

from Tools import gdal_utils

ruta = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\dades\Ag\Ag.tif"
ruta2 = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\outputs_cog"

gdal_utils.mostrar_informe(gdal_utils.inspeccionar_carpeta(ruta[:-7]))
gdal_utils.mostrar_informe(gdal_utils.inspeccionar_carpeta(ruta2))
print(gdal_utils.analizar_cog(ruta))
print(gdal_utils.analizar_cog(ruta2))