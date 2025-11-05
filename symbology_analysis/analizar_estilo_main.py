# 3_analizar_estilo_main.py
import os
# ¡Aquí está la magia!
# Importamos las funciones desde nuestros otros archivos .py
from stylx_utils import get_cims_from_stylx
from cim_parser import find_colors_in_cim

def main():
    """
    Función principal que ejecuta el análisis.
    """
    # --- CONFIGURACIÓN ---
    # 1. Define la ruta a tu estilo
    style_path = r"C:\Users\becari.g.fernandez\Documents\ArcGIS\Projects\Proyecto_de_pruebas\test_style.stylx"
    # -------------------

    # 2. Llamar a la función para obtener todos los CIMs
    # Pon verbose=False si no quieres ver los mensajes de "cargando..."
    all_cims = get_cims_from_stylx(style_path, verbose=True)

    # 3. Analizar los colores de cada CIM encontrado
    print("\n--- 🎨 Análisis de Color de Símbolos ---")

    if not all_cims:
        print("No se encontraron símbolos para analizar.")
    else:
        for item_id, item_info in all_cims.items():
            print(f"\nAnalizando ID: {item_id} (Nombre: {item_info['name']})")
            
            cim_data = item_info['cim_data']
            
            # 4. Usar la función importada para encontrar colores
            colors = find_colors_in_cim(cim_data)
            
            if not colors:
                print("  -> No se encontraron definiciones de color en este símbolo.")
            else:
                print(f"  -> Se encontraron {len(colors)} colores:")
                for i, (color_type, color_values) in enumerate(colors):
                    print(f"    - Color {i+1}: Tipo = {color_type}, Valores = {color_values}")

# Esta construcción le dice a Python que ejecute la función 'main' 
# solo cuando este script es el archivo principal.
if __name__ == "__main__":
    main()