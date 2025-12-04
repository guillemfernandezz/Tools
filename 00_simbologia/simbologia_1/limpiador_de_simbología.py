import sqlite3
import json
import shutil
import os
import sys

# --- CONFIGURACIÓN ---
INPUT_STYLX_PATH = r"C:\Users\becari.g.fernandez\Desktop\treballs\01_simbologia\dades\riscos-geologics-25000-v2r0-202510.stylx"

def clean_geometric_effects(layer_json):
    """
    Busca y elimina efectos geométricos que desplazan el símbolo (Offset, Buffer).
    """
    modified = False
    if "effects" in layer_json and layer_json["effects"]:
        original_count = len(layer_json["effects"])
        
        # Filtramos la lista: Nos quedamos solo con los efectos que NO sean de desplazamiento
        # CIMGeometricEffectOffset -> Culpable habitual
        # CIMGeometricEffectBuffer -> A veces desplaza visualmente
        new_effects = []
        for effect in layer_json["effects"]:
            eff_type = effect.get("type", "")
            if "Offset" in eff_type or "Buffer" in eff_type or "Move" in eff_type:
                print(f"   -> [!] Eliminado Efecto Geométrico: {eff_type}")
                modified = True
            else:
                new_effects.append(effect)
        
        layer_json["effects"] = new_effects
        
    return modified, layer_json

def clean_marker_placement(layer_json):
    modified = False
    
    # 1. Limpieza de Efectos Geométricos (NUEVO)
    eff_mod, layer_json = clean_geometric_effects(layer_json)
    if eff_mod: modified = True

    # 2. Limpieza de Offsets directos (Y/X)
    if "offsetY" in layer_json and layer_json["offsetY"] != 0:
        print(f"   -> Corregido Offset Y: de {layer_json['offsetY']} a 0")
        layer_json["offsetY"] = 0
        modified = True
        
    if "offsetX" in layer_json and layer_json["offsetX"] != 0:
        layer_json["offsetX"] = 0
        modified = True

    # 3. Limpieza de Anchor Point (Efecto Péndulo)
    if "anchorPoint" in layer_json:
        current_anchor = layer_json["anchorPoint"]
        if current_anchor.get("x") != 0 or current_anchor.get("y") != 0 or layer_json.get("anchorPointUnits") != "Relative":
            print(f"   -> Recentrando Anchor Point al centro absoluto (0,0)")
            layer_json["anchorPoint"] = {"x": 0, "y": 0}
            layer_json["anchorPointUnits"] = "Relative"
            modified = True

    # 4. Limpieza de Marker Placement (Offset perpendicular)
    if "markerPlacement" in layer_json:
        placement = layer_json["markerPlacement"]
        # CIMMarkerPlacementAlongLineSameSize es el típico para líneas
        if "offset" in placement and placement["offset"] != 0:
             print(f"   -> Eliminado Offset Perpendicular en MarkerPlacement")
             placement["offset"] = 0
             modified = True

    return modified, layer_json

def process_symbol_content(content_str):
    try:
        data = json.loads(content_str)
    except json.JSONDecodeError:
        return None, False

    modified_symbol = False

    # A. Revisar efectos globales (a nivel de símbolo, no de capa)
    if "effects" in data:
         # Misma lógica de limpieza para efectos globales
         pass # (Generalmente están dentro de symbolLayers, pero por si acaso)

    # B. Revisar capas individuales (symbolLayers)
    if "symbolLayers" in data:
        for layer in data["symbolLayers"]:
            # Procesamos marcadores y también trazos (por si el trazo tiene un offset effect)
            layer_modified, new_layer = clean_marker_placement(layer)
            if layer_modified:
                layer = new_layer
                modified_symbol = True
    
    if modified_symbol:
        return json.dumps(data), True
    else:
        return content_str, False

def main():
    print("--- AUTOMATED STYLX CLEANER V2 (Inc. Effects) ---")
    
    if not os.path.exists(INPUT_STYLX_PATH):
        print(f"ERROR: No encuentro el archivo: {INPUT_STYLX_PATH}")
        return

    new_name = input("Introduce el nombre para el nuevo archivo .stylx: ").strip()
    if not new_name.endswith(".stylx"):
        new_name += ".stylx"
    
    output_dir = os.path.dirname(INPUT_STYLX_PATH)
    output_path = os.path.join(output_dir, new_name)

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"Archivo existente eliminado.")
        except PermissionError:
            print("ERROR: Cierra ArcGIS Pro. El archivo está bloqueado.")
            return
    
    shutil.copy2(INPUT_STYLX_PATH, output_path)

    try:
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT ID, Name, Content FROM ITEMS")
        rows = cursor.fetchall()
        
        updates = 0
        print(f"Analizando {len(rows)} elementos...")

        for row in rows:
            item_id = row[0]
            item_name = row[1]
            content = row[2]
            
            if not content: continue

            new_content, was_modified = process_symbol_content(content)
            
            if was_modified:
                print(f"MODIFICADO: {item_name}")
                cursor.execute("UPDATE ITEMS SET Content = ? WHERE ID = ?", (new_content, item_id))
                updates += 1

        conn.commit()
        conn.close()
        
        print("-" * 30)
        print(f"HECHO. {updates} símbolos corregidos.")
        print(f"Archivo: {output_path}")

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    main()