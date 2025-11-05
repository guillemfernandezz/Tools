# 2_cim_parser.py

def find_colors_in_cim(obj):
    """
    Busca recursivamente en un objeto (dict o list) del CIM
    todas las definiciones de color.

    Args:
        obj (dict or list): El diccionario o lista del CIM donde buscar.

    Returns:
        list: Una lista de tuplas. Cada tupla contiene (tipo_de_color, valores).
            Ej: [('CIMRGBColor', [255, 0, 0, 100]), 
            ('CIMCMYKColor', [0, 100, 100, 0, 100])]
    """
    found_colors = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'color' and isinstance(value, dict) and 'type' in value:
                color_type = value.get('type', 'TipoDesconocido')
                color_values = value.get('values', 'ValoresDesconocidos')
                found_colors.append((color_type, color_values))
            else:
                found_colors.extend(find_colors_in_cim(value))
                
    elif isinstance(obj, list):
        for item in obj:
            found_colors.extend(find_colors_in_cim(item))
            
    return found_colors

# Buena práctica
if __name__ == "__main__":
    print("Este script es una librería.")
    print("Por favor, ejecute '3_analizar_estilo_main.py' para analizar un estilo.")