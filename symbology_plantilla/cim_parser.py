# 2_cim_parser.py
from stylx_utils import get_cims_from_stylx 

def extraer_parametros_plantilla(template_path, symbol_name):
    """
    Abre el stylx de plantilla y ROBA los valores numéricos (Size, Step)
    del símbolo indicado.
    """
    print(f"[DEBUG] Extrayendo parámetros de '{symbol_name}' en {template_path}")
    cims = get_cims_from_stylx(template_path, verbose=False)
    
    params = {
        'size': 12.0, # Valor por defecto si falla
        'stepX': 9.0,
        'stepY': 9.0
    }
    
    found = False
    for item_id, info in cims.items():
        if info['name'] == symbol_name:
            cim = info['cim_data']
            # Buscamos la capa VectorMarker
            for layer in cim.get('symbolLayers', []):
                if layer.get('type') == 'CIMVectorMarker':
                    # ¡ENCONTRADO! Robamos los valores
                    params['size'] = layer.get('size', 12.0)
                    
                    placement = layer.get('markerPlacement', {})
                    params['stepX'] = placement.get('stepX', 9.0)
                    params['stepY'] = placement.get('stepY', 9.0)
                    
                    print(f"[DEBUG] Parámetros robados: Size={params['size']}, Step={params['stepX']}")
                    found = True
                    break
        if found: break
    
    if not found:
        print("[WARN] No se encontró el símbolo plantilla. Usando valores por defecto.")
        
    return params


def extraer_datos_hatch(capa_hatch):
    datos = {'color': None, 'separation': None} 
    try:
        datos['separation'] = capa_hatch.get('separation')
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers:
                datos['color'] = line_layers[0].get('color')
    except: pass 
    return datos


def build_svg_marker_with_params(svg_data_url, hatch_color, template_params, offset_ratio=0.0):
    """
    Crea un marcador SVG nuevo, pero configurado con los parámetros
    (Size, Step) extraídos de la plantilla.
    """
    
    # 1. Usamos los valores robados de la plantilla
    size = template_params['size']
    step_x = template_params['stepX']
    step_y = template_params['stepY']
    
    # 2. Calculamos offset para mrc_
    # Desplazamos en X la mitad del paso definido en la plantilla
    move_x = step_x * offset_ratio
    
    # 3. Construimos el JSON limpio (con el Frame correcto para tu SVG)
    plantilla_svg = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "Capa SVG Final",
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      
      "size": size, # <-- Valor de tu plantilla sidl
      
      "billboardMode3D": "FaceNearPlane",
      "colorLocked": True,
      
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "randomness": 0,
        
        "stepX": step_x, # <-- Valor de tu plantilla sidl
        "stepY": step_y, # <-- Valor de tu plantilla sidl
        
        "offsetX": move_x, # Offset calculado
        "offsetY": 0,
        
        "clipping": "ClipAtBoundary"
      },
      
      # FRAME: Usamos uno genérico que cubra el SVG (0 a 5.2 aprox)
      # Esto soluciona el problema del "shapemarker vacío"
      "frame": { "xmin": 0.0, "ymin": 0.0, "xmax": 5.2, "ymax": 5.2 },
      
      "markerGraphics": [
        {
          "type": "CIMMarkerGraphic",
          "geometry": { "url": svg_data_url }, 
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [
              {
                "type": "CIMSolidFill", 
                "enable": True,
                "color": hatch_color # CMYK Original
              },
              # Añadimos borde del mismo color para evitar líneas negras
              {
                "type": "CIMSolidStroke", 
                "enable": True,
                "width": 0, 
                "color": hatch_color 
              }
            ],
            "angleAlignment": "Map"
          }
        }
      ],
      "scaleSymbolsProportionally": True,
      "respectFrame": True
    }
    
    return plantilla_svg