# 2_cim_parser.py
import copy
import re
from stylx_utils import get_cims_from_stylx 

def extraer_parametros_plantilla(template_path, symbol_name):
    """
    Roba Size y Step de la plantilla (test.stylx).
    """
    print(f"[DEBUG] Extrayendo parámetros de '{symbol_name}'")
    cims = get_cims_from_stylx(template_path, verbose=False)
    params = {'size': 12.0, 'stepX': 9.0, 'stepY': 9.0} # Defaults
    
    for item_id, info in cims.items():
        if info['name'] == symbol_name:
            cim = info['cim_data']
            for layer in cim.get('symbolLayers', []):
                if layer.get('type') == 'CIMVectorMarker':
                    params['size'] = layer.get('size', 12.0)
                    placement = layer.get('markerPlacement', {})
                    params['stepX'] = placement.get('stepX', 9.0)
                    params['stepY'] = placement.get('stepY', 9.0)
                    print(f"[DEBUG] Parámetros plantilla: Size={params['size']}, Step={params['stepX']}")
                    return params
    return params

def parse_svg_geometry(svg_content):
    """
    Lee el texto del SVG y convierte el path 'd' en coordenadas CIM 'rings'.
    Maneja la transformación 'translate(0,5.06) scale(1, -1)' específica de tu archivo.
    """
    print("[DEBUG] Parseando geometría del SVG...")
    try:
        # 1. Buscar el atributo 'd' del path
        d_match = re.search(r' d="([^"]+)"', svg_content)
        if not d_match:
            print("[ERROR] No se encontró el atributo d=\"...\" en el SVG")
            return None
            
        d_str = d_match.group(1)
        
        # 2. Parsear comandos simples (M x,y l dx,dy ... z)
        # Limpiamos letras y separamos
        parts = d_str.replace('M', '').replace('l', '').replace('z', '').replace(',', ' ').split()
        floats = [float(x) for x in parts if x.strip()]
        
        coords = []
        current_x, current_y = 0.0, 0.0
        
        # El primer punto es absoluto (M), los siguientes son relativos (l)
        if len(floats) >= 2:
            current_x, current_y = floats[0], floats[1]
            coords.append([current_x, current_y])
            
            i = 2
            while i < len(floats) - 1:
                dx, dy = floats[i], floats[i+1]
                current_x += dx
                current_y += dy
                coords.append([current_x, current_y])
                i += 2
        
        # 3. Aplicar Transformación (Espejo vertical y traslación)
        # Tu SVG tiene: transform="translate(0,5.06) scale(1, -1)"
        # Esto significa: y_final = 5.06 + (y_original * -1)  =>  5.06 - y
        
        HEIGHT_OFFSET = 5.06 # Sacado de tu SVG
        
        transformed_rings = []
        for pt in coords:
            x, y = pt[0], pt[1]
            new_y = HEIGHT_OFFSET - y
            transformed_rings.append([x, new_y])
            
        # Cerrar el anillo si es necesario
        if transformed_rings[0] != transformed_rings[-1]:
            transformed_rings.append(transformed_rings[0])
            
        # Calcular Frame dinámico (Bounding Box)
        xs = [p[0] for p in transformed_rings]
        ys = [p[1] for p in transformed_rings]
        frame = {
            "xmin": min(xs), "ymin": min(ys),
            "xmax": max(xs), "ymax": max(ys)
        }
        
        print(f"[DEBUG] Geometría parseada con éxito. Puntos: {len(transformed_rings)}")
        return [transformed_rings], frame

    except Exception as e:
        print(f"[ERROR] Fallo al parsear SVG manualmente: {e}")
        return None, None

def extraer_datos_hatch(capa_hatch):
    datos = {'color': None} 
    try:
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers:
                datos['color'] = line_layers[0].get('color')
    except: pass 
    return datos

def build_svg_geometry_marker(svg_rings, svg_frame, hatch_color, template_params, offset_ratio=0.0):
    """
    Construye el marcador final usando:
    - Geometría: Extraída del SVG (Rings)
    - Config: De la plantilla (Size, Step)
    - Color: Del Hatch (CMYK)
    """
    
    size = template_params['size']
    step_x = template_params['stepX']
    step_y = template_params['stepY']
    move_x = step_x * offset_ratio
    
    plantilla = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "SVG Geometría Parseada",
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      
      "size": size, # <-- De tu plantilla test.stylx
      "frame": svg_frame, # <-- Calculado del SVG
      
      "billboardMode3D": "FaceNearPlane",
      "colorLocked": True,
      
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "randomness": 0,
        "stepX": step_x, # <-- De tu plantilla
        "stepY": step_y,
        "offsetX": move_x,
        "offsetY": 0,
        "clipping": "ClipAtBoundary"
      },
      
      "markerGraphics": [
        {
          "type": "CIMMarkerGraphic",
          # ¡AQUÍ USAMOS LA GEOMETRÍA PARSEADA DEL SVG!
          "geometry": { 
              "rings": svg_rings 
          }, 
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [
              {
                "type": "CIMSolidFill", 
                "enable": True,
                "color": hatch_color # CMYK Original
              }
              # Quitamos el borde stroke para que no engorde, o lo añadimos con width=0
            ],
            "angleAlignment": "Map"
          }
        }
      ],
      "scaleSymbolsProportionally": True,
      "respectFrame": True
    }
    
    return plantilla