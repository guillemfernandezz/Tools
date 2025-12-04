# 2_cim_parser.py
import copy
from stylx_utils import get_cims_from_stylx 

# ¡Esta función ya no es necesaria!
# def get_template_layer(...):
#    ...

def extraer_color_hatch(capa_hatch):
    """
    Extrae únicamente el objeto de color CMYK
    de una capa CIMHatchFill.
    """
    print("    [DEBUG] Ejecutando 'extraer_color_hatch'...")
    
    try:
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers and isinstance(line_layers, list) and len(line_layers) > 0:
                stroke_layer = line_layers[0] 
                color = stroke_layer.get('color')
                print(f"    [DEBUG] Objeto de color extraído: {color}")
                return color
            else:
                print("    [DEBUG] 'line_layers' está vacío o no es una lista.")
        else:
            print("    [DEBUG] No se encontró 'lineSymbol'.")

    except Exception as e:
        print(f"    [DEBUG] Error crítico en 'extraer_color_hatch': {e}")
        pass 

    print("    [DEBUG] ¡FALLO! No se pudo extraer el color.")
    return None


def build_marker_layer_from_hybrid_template(hatch_color):
    """
    Construye la capa CIMVectorMarker usando la GEOMETRÍA
    de '_plantilla_svg.json' (para compatibilidad VTPK)
    pero con los PARÁMETROS de 'sidl.stylx' (para la apariencia).
    """
    print(f"    [DEBUG] Ejecutando 'build_marker_layer_from_hybrid_template' con color: {hatch_color}")

    # Plantilla basada en _plantilla_svg.json 
    plantilla_hibrida = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "Capa SVG Híbrida (VTPK)", 
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      "billboardMode3D": "FaceNearPlane",
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed", # ¡Importante para VTPK!
        "clipping": "ClipAtBoundary"
      },
      "markerGraphics": [
        {
          "type": "CIMMarkerGraphic",
          # Geometría DIAGONAL (de _plantilla_svg.json)
          "geometry": { 
            "rings": [ [ [ 5.12, 0.3 ], [ 4.87, 0.06 ], [ 4.87, 0.06 ], [ 0.06, 4.87 ], [ 0.3, 5.12 ], [ 5.12, 0.3 ] ] ]
          },
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [ { "type": "CIMSolidFill", "enable": True } ]
          }
        },
        {
          "type": "CIMMarkerGraphic",
          "geometry": { 
            "rings": [ [ [ 4.87, 0.06 ], [ 5.12, 0.3 ], [ 0.3, 5.12 ], [ 0.06, 4.87 ], [ 4.87, 0.06 ], [ 4.87, 0.06 ] ] ]
          },
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [ { "type": "CIMSolidStroke", "enable": True } ]
          }
        }
      ],
      "scaleSymbolsProportionally": True,
      "respectFrame": True
    }
    
    # --- Inyectamos los valores ---
    
    # 1. Parámetros de 'sidl.stylx'  (Tú petición de "más finas" y separación)
    nueva_capa_svg = copy.deepcopy(plantilla_hibrida)
    
    nueva_capa_svg["size"] = 12.0
    nueva_capa_svg["markerPlacement"]["stepX"] = 9.0
    nueva_capa_svg["markerPlacement"]["stepY"] = 9.0
    
    # 2. Relleno (markerGraphics[0])
    nueva_capa_svg["markerGraphics"][0]["symbol"]["symbolLayers"][0]["color"] = hatch_color
    
    # 3. Trazo (markerGraphics[1])
    stroke_layer = nueva_capa_svg["markerGraphics"][1]["symbol"]["symbolLayers"][0]
    stroke_layer["color"] = hatch_color
    stroke_layer["width"] = 0.1 # Grosor de 0.1 de 'sidl.stylx' 

    print(f"    [DEBUG] Plantilla JSON (HÍBRIDA) construida. Size: 12.0, Sep: 9.0, Ancho: 0.1")
    
    return nueva_capa_svg


if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute 'aplicar_plantilla_final.py' para ejecutar la modificación.")