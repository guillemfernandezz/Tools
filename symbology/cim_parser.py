# 2_cim_parser.py
from stylx_utils import get_cims_from_stylx 

def extraer_datos_hatch(capa_hatch):
    """
    Extrae el objeto de color, la separación Y el ancho de línea.
    """
    print("    [DEBUG] Ejecutando 'extraer_datos_hatch'...")
    datos = {'color': None, 'separation': None, 'width': 0.2} 
    
    try:
        datos['separation'] = capa_hatch.get('separation')
        
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers and isinstance(line_layers, list) and len(line_layers) > 0:
                stroke_layer = line_layers[0] 
                datos['color'] = stroke_layer.get('color')
                datos['width'] = stroke_layer.get('width', 0.2) 
    except Exception as e:
        print(f"    [DEBUG] Error parseando hatch: {e}")
        pass 

    return datos


def build_geometric_marker_layer(hatch_color, separation, hatch_width, offset_ratio=0.0, custom_width=None, separation_factor=1.42):
    """
    Construye un CIMVectorMarker con geometría generada.
    
    CAMBIOS V11:
    - 'separation_factor': Multiplicador para corregir la densidad (Default 1.42).
    """
    print(f"    [DEBUG] Generando Geometría (Offset: {offset_ratio}, Factor Sep: {separation_factor})...")

    # 1. AJUSTE DE SEPARACIÓN (MATEMÁTICO)
    # Multiplicamos la separación original por el factor (idealmente 1.4142 para diagonales)
    step = separation * separation_factor
    
    # 2. CÁLCULO DEL OFFSET
    # El desplazamiento debe ser proporcional al NUEVO paso (step)
    move_x = step * offset_ratio
    move_y = 0 
    
    # 3. GEOMETRÍA MATEMÁTICA (Diagonal '\')
    # Extendemos un 10% para asegurar solapamiento y evitar líneas a trazos
    pad = step * 0.1
    x1, y1 = -pad, step + pad
    x2, y2 = step + pad, -pad
    path_coords = [ [x1, y1], [x2, y2] ]
    
    # 4. AJUSTE DE GROSOR
    if custom_width is not None:
        line_width = custom_width
    else:
        line_width = hatch_width / 2.0
    
    plantilla_geometrica = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "Diagonal Generada V11",
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      "size": step, # El tamaño de la caja sigue al paso
      "billboardMode3D": "FaceNearPlane",
      "colorLocked": True,
      
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "randomness": 0,
        "stepX": step,
        "stepY": step,
        "offsetX": move_x,
        "offsetY": move_y,
        "clipping": "ClipAtBoundary"
      },
      "frame": { "xmin": 0.0, "ymin": 0.0, "xmax": step, "ymax": step },
      
      "markerGraphics": [
        {
          "type": "CIMMarkerGraphic",
          "geometry": {
            "paths": [ path_coords ]
          },
          "symbol": {
            "type": "CIMLineSymbol",
            "symbolLayers": [
              {
                "type": "CIMSolidStroke",
                "enable": True,
                "capStyle": "Square",
                "joinStyle": "Miter",
                "lineStyle3D": "Strip",
                "miterLimit": 10,
                "width": line_width,
                "color": hatch_color # CMYK Original
              }
            ]
          }
        }
      ],
      "scaleSymbolsProportionally": True,
      "respectFrame": True
    }

    return plantilla_geometrica

if __name__ == "__main__":
    print("Librería lista.")