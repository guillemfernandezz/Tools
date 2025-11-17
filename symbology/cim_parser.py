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


def build_geometric_marker_layer(hatch_color, separation, hatch_width, offset_ratio=0.0, custom_width=None):
    """
    Construye un CIMVectorMarker con geometría generada.
    
    CAMBIOS V10:
    - Soporte para 'custom_width' (grosor fijo manual).
    - Offset corregido: Solo desplaza en X para evitar solapamiento en diagonales.
    """
    print(f"    [DEBUG] Generando Geometría (Offset Ratio: {offset_ratio})...")

    # 1. AJUSTE DE SEPARACIÓN
    # Mantenemos el 1.5 que te gustó, o el 1.0 de la plantilla. 
    # Si quieres que sea idéntico a tu plantilla 'sidl', debería ser 1.0, 
    # pero dijiste que el anterior estaba "casi" bien. Lo dejaré en 1.0 para ser fiel a 'sidl'.
    step = separation 
    
    # 2. CÁLCULO DEL OFFSET (CORREGIDO PARA MRC)
    # Solo desplazamos en X. Si desplazamos X e Y, movemos la línea a lo largo de su propio eje.
    move_x = step * offset_ratio
    move_y = 0 # No desplazamos Y para asegurar el intercalado horizontal
    
    # 3. GEOMETRÍA MATEMÁTICA (Diagonal '\')
    pad = step * 0.1
    x1, y1 = -pad, step + pad
    x2, y2 = step + pad, -pad
    path_coords = [ [x1, y1], [x2, y2] ]
    
    # 4. AJUSTE DE GROSOR (LÓGICA NUEVA)
    if custom_width is not None:
        line_width = custom_width
        print(f"    [DEBUG] Usando grosor personalizado: {line_width}")
    else:
        line_width = hatch_width / 2.0
        print(f"    [DEBUG] Usando grosor calculado: {line_width}")
    
    plantilla_geometrica = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "Diagonal Generada V10",
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      "size": step,
      "billboardMode3D": "FaceNearPlane",
      "colorLocked": True,
      
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "randomness": 0,
        "stepX": step,
        "stepY": step,
        
        # --- OFFSET CORREGIDO ---
        "offsetX": move_x,
        "offsetY": move_y, 
        # ------------------------
        
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