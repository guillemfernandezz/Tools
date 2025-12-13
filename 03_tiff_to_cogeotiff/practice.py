import sys
import os

# 1. Configurar rutas
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_arriba = os.path.dirname(carpeta_actual) 
sys.path.append(carpeta_arriba)

# 2. EL CAMBIO CLAVE ESTÁ AQUÍ:
# from Carpeta.Archivo import Funcion
from Tools.batch_polygon_to_raster import batch_polygon_to_raster

# 3. Definir variables
aprx_path = r"C:\Users\Usuario\Desktop\Temporal\ICGC\TestTool\TestTool.aprx"
map_name = "Map"

# 4. Ejecutar
batch_polygon_to_raster(aprx_path, map_name)