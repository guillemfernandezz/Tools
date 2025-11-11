# 2_cim_parser.py

def extraer_datos_de_hatch(capa_hatch):
    """
    Extrae el objeto de color y la separación de una capa CIMHatchFill.
    Esta versión está ajustada Específicamente a la estructura del
    archivo 'geologia-territorial-50000-geologic-v3r0-202412.stylx'.
    """
    datos = {'color': None, 'separation': None, 'width': 0.2} # Añadimos ancho por defecto
    
    try:
        # 1. Extraer la separación
        datos['separation'] = capa_hatch.get('separation')
        
        # 2. Extraer el color y el ancho (Ruta directa y robusta)
        line_symbol = capa_hatch.get('lineSymbol')
        if line_symbol:
            line_layers = line_symbol.get('symbolLayers')
            if line_layers and isinstance(line_layers, list) and len(line_layers) > 0:
                # El color y el ancho están en el primer 'symbolLayer' (CIMSolidStroke)
                stroke_layer = line_layers[0]
                datos['color'] = stroke_layer.get('color')
                # También extraemos el ancho de línea original, por si acaso
                if 'width' in stroke_layer:
                    datos['width'] = stroke_layer.get('width')

    except Exception as e:
        print(f"Error parseando un hatch: {e}")
        pass 

    return datos


def build_svg_marker(color_obj, svg_data_url, separacion, tamano_pt=18.0, line_width=0.2):
    """
    Construye la estructura JSON completa para un CIMMarkerFill
    que usa un CIMVectorMarker (SVG).
    
    ¡VERSIÓN CORREGIDA! 
    Aplica CIMSolidStroke (trazo) en lugar de CIMSolidFill (relleno).
    Usa el color original (CMYK) sin convertir.
    """
    
    step = separacion if separacion and separacion > 0 else 10.0
    
    # Esta es la plantilla JSON para el reemplazo
    marker_fill_json = {
      "type": "CIMMarkerFill",
      "enable": True,
      "name": "Capa SVG Reemplazada",
      "markerPlacement": {
        "type": "CIMMarkerPlacementInsidePolygon",
        "gridType": "Fixed",
        "stepX": step,
        "stepY": step,
        "clipping": "ClipAtBoundary"
      },
      "marker": {
        "type": "CIMVectorMarker",
        "enable": True,
        "size": tamano_pt,
        "frame": { "xmin": 0, "ymin": 0, "xmax": 16, "ymax": 16 },
        "markerGraphics": [
          {
            "type": "CIMMarkerGraphic",
            "geometry": { "url": svg_data_url },
            
            # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
            "symbol": {
              # El SVG se trata como una LÍNEA
              "type": "CIMLineSymbol", 
              "symbolLayers": [
                {
                  # Le aplicamos un TRAZO, no un relleno
                  "type": "CIMSolidStroke", 
                  "enable": True,
                  "capStyle": "Round", # Añadimos valores por defecto
                  "joinStyle": "Round",
                  "width": line_width, # Usamos el ancho del hatch original
                  "color": color_obj  # ¡Usamos el color CMYK original!
                }
              ]
            }
            # --- FIN DE LA CORRECCIÓN ---
          }
        ],
        "respectFrame": True
      }
    }
    
    return marker_fill_json


# Esta parte es solo para que el script no se ejecute si se llama por error
if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute 'actualizar_estilo_main.py' para ejecutar la modificación.")