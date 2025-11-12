# 2_cim_parser.py
import copy # Usaremos esto para copiar la plantilla

def extraer_datos_hatch(capa_hatch):
    """
    Extrae el objeto de color CMYK, la separación Y el ancho de línea
    de una capa CIMHatchFill.
    """
    print("    [DEBUG] Ejecutando 'extraer_datos_hatch'...")
    datos = {'color': None, 'separation': None, 'width': 0.2} 
    
    try:
        datos['separation'] = capa_hatch.get('separation')
        print(f"    [DEBUG] Separación extraída: {datos['separation']}")
        
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers and isinstance(line_layers, list) and len(line_layers) > 0:
                stroke_layer = line_layers[0] 
                datos['color'] = stroke_layer.get('color')
                datos['width'] = stroke_layer.get('width', 0.2) 
                print(f"    [DEBUG] Objeto de color extraído: {datos['color']}")
                print(f"    [DEBUG] Ancho de línea extraído: {datos['width']}")
            else:
                print("    [DEBUG] 'line_layers' está vacío o no es una lista.")
        else:
            print("    [DEBUG] No se encontró 'lineSymbol'.")

    except Exception as e:
        print(f"    [DEBUG] Error crítico en 'extraer_datos_hatch': {e}")
        pass 

    if not datos['color']:
        print("    [DEBUG] ¡FALLO! No se pudo extraer el color.")
    if not datos['separation']:
        print("    [DEBUG] ¡FALLO! No se pudo extraer la separación.")
        
    return datos


def build_svg_marker_layer(hatch_color, separation, hatch_width):
    """
    Construye la capa CIMVectorMarker completa, basándose en la
    plantilla extraída de '_plantilla_svg.json'.
    
    VERSIÓN V3-TEST:
    - size: 18.0 (Grande, para asegurar línea continua)
    - separation: x1.5 (Ajuste intermedio)
    - width: /2 (Más fino)
    """
    print(f"    [DEBUG] Ejecutando 'build_svg_marker_layer' con color: {hatch_color}")

    # Esta es la plantilla COMPLETA de la capa CIMVectorMarker
    # Copiada directamente de tu archivo _plantilla_svg.json
    plantilla_vector_marker = {
      "type": "CIMVectorMarker",
      "enable": True,
      "name": "Capa SVG Ajustada (V3)", 
      "anchorPointUnits": "Relative",
      "dominantSizeAxis3D": "Y",
      "size": 18.0, # <-- ¡CAMBIO 1: Volvemos a 18.0 para asegurar la superposición!
      "billboardMode3D": "FaceNearPlane",
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "randomness": 0, 
        "seed": 938511,
        "stepX": 16, # Valor que se reemplazará
        "stepY": 16, # Valor que se reemplazará
        "clipping": "ClipAtBoundary"
      },
      "frame": { "xmin": 0.0, "ymin": 0.0, "xmax": 5.19, "ymax": 5.19 },
      "markerGraphics": [
        {
          "type": "CIMMarkerGraphic",
          "geometry": { 
            "rings": [ [ [ 5.12, 0.3 ], [ 4.87, 0.06 ], [ 4.87, 0.06 ], [ 0.06, 4.87 ], [ 0.3, 5.12 ], [ 5.12, 0.3 ] ] ]
          },
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [
              {
                "type": "CIMSolidFill", 
                "enable": True,
                "color": { "type": "CIMCMYKColor", "values": [ 100, 25, 100, 0, 100 ] } # Se reemplazará
              }
            ],
            "angleAlignment": "Map"
          }
        },
        {
          "type": "CIMMarkerGraphic",
          "geometry": { 
            "rings": [ [ [ 4.87, 0.06 ], [ 5.12, 0.3 ], [ 0.3, 5.12 ], [ 0.06, 4.87 ], [ 4.87, 0.06 ], [ 4.87, 0.06 ] ] ]
          },
          "symbol": {
            "type": "CIMPolygonSymbol",
            "symbolLayers": [
              {
                "type": "CIMSolidStroke", 
                "enable": True,
                "capStyle": "Butt",
                "joinStyle": "Miter",
                "lineStyle3D": "Strip",
                "miterLimit": 4,
                "width": 0.2, # Se reemplazará
                "color": { "type": "CIMRGBColor", "values": [ 0, 0, 0, 100 ] } # Se reemplazará
              }
            ],
            "angleAlignment": "Map"
          }
        }
      ],
      "scaleSymbolsProportionally": True,
      "respectFrame": True
    }
    
    nueva_capa_svg = copy.deepcopy(plantilla_vector_marker)
    
    # --- Inyectamos los valores extraídos ---
    
    # 1. Inyectar separación (¡CAMBIO 2: Separación intermedia!)
    nueva_capa_svg["markerPlacement"]["stepX"] = separation * 1.5
    nueva_capa_svg["markerPlacement"]["stepY"] = separation * 1.5
    
    # 2. Inyectar color en el RELLENO (markerGraphics[0])
    nueva_capa_svg["markerGraphics"][0]["symbol"]["symbolLayers"][0]["color"] = hatch_color
    
    # 3. Inyectar EL MISMO color en el TRAZO (markerGraphics[1])
    nueva_capa_svg["markerGraphics"][1]["symbol"]["symbolLayers"][0]["color"] = hatch_color
    
    # 4. Inyectar ancho de línea en el TRAZO (¡CAMBIO 3: Más fino!)
    nueva_capa_svg["markerGraphics"][1]["symbol"]["symbolLayers"][0]["width"] = hatch_width / 2.0

    print(f"    [DEBUG] Plantilla JSON (Fill+Stroke) (V3_TEST) construida y rellenada con éxito.")
    
    return nueva_capa_svg


if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute 'actualizar_estilo_main.py' para ejecutar la modificación.")