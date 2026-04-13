import os
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom

def force_pam_injection(tif_path, csv_path):
    print(f"--- 💉 INYECCIÓN FORZOSA DE RAT EN: {os.path.basename(tif_path)} ---")

    if not os.path.exists(csv_path):
        print("❌ ERROR: No encuentro el CSV.")
        return

    # 1. Leer el CSV (Diccionario Valor -> Texto)
    data_map = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader) # Leer cabecera
            
            # Buscamos índices dinámicamente
            # Asumimos que Value es la primera o se llama 'Value'
            try:
                idx_val = next(i for i, h in enumerate(headers) if 'value' in h.lower())
            except:
                idx_val = 0 # Fallback al primero
            
            # Buscamos texto
            try:
                idx_txt = next(i for i, h in enumerate(headers) if 'rang' in h.lower() or 'conc' in h.lower())
            except:
                print("❌ ERROR: El CSV no tiene columna de texto ('rang' o 'conc').")
                return

            print(f"  > Leyendo columnas: Value[{idx_val}], Texto[{idx_txt}]")

            for row in reader:
                if row:
                    try:
                        val = int(float(row[idx_val])) # Asegurar entero
                        txt = row[idx_txt]
                        data_map[val] = txt
                    except:
                        pass
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return

    print(f"  > Datos cargados: {len(data_map)} clases.")

    # 2. Construir el XML PAM desde cero (Lo más seguro)
    root = ET.Element("PAMDataset")
    band = ET.SubElement(root, "PAMRasterBand", band="1")
    
    # Aquí está la clave que faltaba en tu archivo:
    rat = ET.SubElement(band, "GDALRasterAttributeTable")

    # Definición de columnas
    # Col 0: Value
    fdef_val = ET.SubElement(rat, "FieldDefn", index="0")
    ET.SubElement(fdef_val, "Name").text = "Value"
    ET.SubElement(fdef_val, "Type").text = "0" # Integer
    ET.SubElement(fdef_val, "Usage").text = "0" 

    # Col 1: Class_Name (El Texto)
    fdef_txt = ET.SubElement(rat, "FieldDefn", index="1")
    ET.SubElement(fdef_txt, "Name").text = "Class_Name"
    ET.SubElement(fdef_txt, "Type").text = "2" # String
    ET.SubElement(fdef_txt, "Usage").text = "0"

    # Inyectar filas
    # Es importante ordenar por Value
    for val in sorted(data_map.keys()):
        row = ET.SubElement(rat, "Row", index=str(val)) # El index suele ser relativo al orden, no al valor, pero GDAL es flexible
        ET.SubElement(row, "F").text = str(val)
        ET.SubElement(row, "F").text = str(data_map[val])

    # 3. Escribir al disco
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    xml_path = tif_path + ".aux.xml"
    
    try:
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"✅ ¡ÉXITO! XML sobrescrito correctamente en:\n   {xml_path}")
    except Exception as e:
        print(f"❌ Error escribiendo archivo: {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # ¡PON TUS RUTAS REALES AQUÍ!
    mi_tif = r"C:\Temp\ArcGIS\Exportaciones\Alumini_raster.tif" 
    mi_csv = r"C:\Temp\ArcGIS\Exportaciones\Alumini_raster.csv"
    
    force_pam_injection(mi_tif, mi_csv)