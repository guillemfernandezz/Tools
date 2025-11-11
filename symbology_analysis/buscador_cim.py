# 3_analizar_estilo_main.py
import os
# ¡Aquí está la magia!
# Importamos las funciones desde nuestros otros archivos .py
from stylx_utils import get_cims_from_stylx

# --- MODIFICACIÓN 1: Importar la nueva función ---
from cim_parser import find_colors_in_cim, filtrar_simbolos_por_hatch

def main():
    """
    Función principal que ejecuta el análisis.
    """
    # --- CONFIGURACIÓN ---
    # 1. Define la ruta a tu estilo
    style_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\00_simbologia\geologia-territorial-50000-geologic-v3r0_living_atlas.stylx"
    
    # --- MODIFICACIÓN 2: Elige qué análisis ejecutar ---
    # Pon True para ejecutar un análisis, False para saltarlo.
    ANALIZAR_COLORES = False
    BUSCAR_SIMBOLOS_HATCH = True
    # -------------------

    # 3. Llamar a la función para obtener todos los CIMs (Esto siempre se hace)
    # Pon verbose=False si no quieres ver los mensajes de "cargando..."
    all_cims = get_cims_from_stylx(style_path, verbose=True)

    if not all_cims:
        print("No se encontraron símbolos para analizar. Saliendo.")
        return # Salimos de la función si no hay nada que hacer

    # --- MODIFICACIÓN 3: Lógica condicional para ejecutar análisis ---

    if ANALIZAR_COLORES:
        print("\n--- 🎨 Análisis de Color de Símbolos ---")
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

    if BUSCAR_SIMBOLOS_HATCH:
        print("\n--- 🚧 Búsqueda de Símbolos con 'Hatch' ---")
        
        # 5. Usar la nueva función importada
        nombres_con_hatch = filtrar_simbolos_por_hatch(all_cims)
        
        if not nombres_con_hatch:
            print("  -> ¡Perfecto! No se encontraron símbolos con 'CIMHatchFill'.")
        else:
            print(f"  -> ¡Atención! Se encontraron {len(nombres_con_hatch)} símbolos con 'CIMHatchFill':")
            for nombre in nombres_con_hatch:
                print(f"    - {nombre}")


# Esta construcción le dice a Python que ejecute la función 'main' 
# solo cuando este script es el archivo principal.
if __name__ == "__main__":
    main()