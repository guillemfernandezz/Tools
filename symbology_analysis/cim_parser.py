# 2_cim_parser.py
import copy
from stylx_utils import get_cims_from_stylx # ¡Necesitamos esto!

def get_template_layer(template_stylx_path, template_symbol_name):
    """
    Carga el .stylx de plantilla y extrae la capa CIMVectorMarker.
    """
    print(f"[DEBUG] Cargando símbolos desde la plantilla: {template_stylx_path}")
    template_cims = get_cims_from_stylx(template_stylx_path, verbose=False)
    
    for item_id, item_info in template_cims.items():
        if item_info.get('name') == template_symbol_name:
            print(f"[DEBUG] Símbolo plantilla '{template_symbol_name}' encontrado.")
            cim_data = item_info.get('cim_data', {})
            symbol_layers = cim_data.get('symbolLayers', [])
            
            for layer in symbol_layers:
                if layer.get('type') == 'CIMVectorMarker':
                    print("[DEBUG] ¡Capa 'CIMVectorMarker' encontrada y extraída como plantilla maestra!")
                    # Devolvemos la capa de plantilla
                    return layer 
                    
    print(f"[DEBUG] ¡FALLO! No se encontró un 'CIMVectorMarker' en el símbolo '{template_symbol_name}'.")
    return None


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


def build_svg_marker_layer(plantilla_maestra, hatch_color, separation, hatch_width):
    """
    Toma la plantilla maestra del CIMVectorMarker y le inyecta
    los valores extraídos del hatch.
    
    VERSIÓN V4-FINAL (Basada en sidl.stylx):
    - size: 12.0 (Fiel a la plantilla 'sidl.stylx')
    - separation: x1.0 (Fiel a la plantilla 'sidl.stylx')
    - width: /2 (Tu petición de "más finas")
    """
    print(f"    [DEBUG] Ejecutando 'build_svg_marker_layer' con color: {hatch_color}")
    
    nueva_capa_svg = copy.deepcopy(plantilla_maestra)
    
    # --- 1. Inyectar Tamaño ---
    # Usamos el 'size' de tu plantilla manual 'sidl.stylx' 
    nueva_capa_svg["size"] = 12.0 
    
    # --- 2. Inyectar Separación ---
    # Usamos la separación ORIGINAL, sin multiplicador, 
    # tal como en tu plantilla 'sidl.stylx' 
    nueva_capa_svg["markerPlacement"]["stepX"] = separation
    nueva_capa_svg["markerPlacement"]["stepY"] = separation
    
    # --- 3. Inyectar Grosor (Más fino) ---
    nuevo_ancho = hatch_width / 2.0
    
    # --- 4. Inyectar Colores ---
    # Relleno (markerGraphics[0])
    nueva_capa_svg["markerGraphics"][0]["symbol"]["symbolLayers"][0]["color"] = hatch_color
    
    # Trazo (markerGraphics[1])
    nueva_capa_svg["markerGraphics"][1]["symbol"]["symbolLayers"][0]["color"] = hatch_color
    nueva_capa_svg["markerGraphics"][1]["symbol"]["symbolLayers"][0]["width"] = nuevo_ancho

    print(f"    [DEBUG] Plantilla JSON (FINAL) construida. Size: 12.0, Sep: {separation}, Ancho: {nuevo_ancho}")
    
    return nueva_capa_svg


if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute 'aplicar_plantilla_final.py' para ejecutar la modificación.")