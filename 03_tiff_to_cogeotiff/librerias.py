import arcpy
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import re  # <--- FALTABA ESTO

# =============================================================================
# 🧠 HELPER FUNCTIONS (Privadas)
# =============================================================================

def _parse_range_text(text):
    """
    (Helper Privado) Parsea texto de rangos a float usando Regex.
    Ej: "entre 1,5 y 2,0" -> (1.5, 2.0)
    """
    if not text: return 0.0, 0.0
    
    # Limpieza: minúsculas y coma decimal a punto
    clean_txt = str(text).lower().replace(',', '.')
    
    # Regex: Busca números (enteros o decimales)
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", clean_txt)]
    
    if not nums: return 0.0, 0.0

    # Lógica de Negocio
    if any(x in clean_txt for x in ['menys', 'menos', '<']):
        return 0.0, nums[0]
    elif any(x in clean_txt for x in ['entre', '-']):
        return (nums[0], nums[1]) if len(nums) >= 2 else (nums[0], nums[0])
    elif any(x in clean_txt for x in ['més', 'mas', '>', 'igual']):
        return nums[0], 999.9 # Techo lógico
    
    return nums[0], nums[0]

# =============================================================================
# 🚀 CORE FUNCTIONS
# =============================================================================

def export_to_cog_arcpy(input_raster, output_folder, method="LZW"):
    """Genera un COG optimizado para datos discretos (U4/U8)."""
    
    TYPE_TRANSLATION = {
        "U1": "1_BIT", "U2": "2_BIT", "U4": "4_BIT",
        "U8": "8_BIT_UNSIGNED", "S8": "8_BIT_SIGNED",
        "U16": "16_BIT_UNSIGNED", "S16": "16_BIT_SIGNED",
        "U32": "32_BIT_UNSIGNED", "S32": "32_BIT_SIGNED",
        "F32": "32_BIT_FLOAT", "F64": "64_BIT"
    }

    if hasattr(input_raster, "name"):
        raw_name = input_raster.name
    else:
        raw_name = os.path.basename(str(input_raster))

    safe_name = raw_name.replace(" ", "_").replace(".", "")
    print(f"--- ⚙️ GENERANDO COG: {raw_name} ---")
    
    if not os.path.exists(output_folder):
        try: os.makedirs(output_folder)
        except: pass
        
    output_path = os.path.join(output_folder, f"{safe_name}.tif")
    
    try:
        desc = arcpy.Describe(input_raster)
        nodata_val = desc.noDataValue if hasattr(desc, 'noDataValue') else None
        raw_type = desc.pixelType 
        target_type = TYPE_TRANSLATION.get(raw_type, raw_type) 
        
        print(f"    > Config: {raw_type} -> {target_type} | NoData: {nodata_val}")
        
        arcpy.management.CopyRaster(
            in_raster=input_raster,
            out_rasterdataset=output_path,
            config_keyword="",
            background_value=None,
            nodata_value=nodata_val,
            onebit_to_eightbit="NONE",   # <--- CORREGIDO (Era 'eightbit')
            colormap_to_RGB="NONE",
            pixel_type=target_type,
            format="COG",
            transform=False
        )
        
        print(f"    ✅ COG guardado: {output_path}")
        return output_path # Devolvemos la ruta para usarla después
    
    except Exception as e:
        print(f"❌ ERROR con {raw_name}: {str(e)}")
        if "000800" in str(e):
            print(f"      [DEBUG] Falló tipo de píxel: {target_type}")
        return None

def generate_gdal_pam_xml(cog_path, csv_path):
    """Genera metadatos PAM (.aux.xml) definiendo la columna de texto como NOMBRE."""
    print(f"--- 💉 INYECTANDO METADATOS PAM (USO: NAME) ---")
    
    if not cog_path or not os.path.exists(cog_path):
        print("  ❌ No existe el COG base.")
        return False

    xml_path = cog_path + ".aux.xml"
    rows_data = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames
            # Búsqueda insensible a mayúsculas
            field_val = next((c for c in cols if c.lower() == 'value'), cols[0]) 
            field_txt = next((c for c in cols if 'rang' in c.lower() or 'conc' in c.lower()), None)
            
            if not field_txt:
                print("  ❌ No encuentro columna de texto en el CSV.")
                return False

            for row in reader:
                # Guardamos como entero y texto limpio
                rows_data.append((int(row[field_val]), row[field_txt]))
                
    except Exception as e:
        print(f"  ❌ Error leyendo CSV: {e}")
        return False

    # XML Construction
    root = ET.Element("PAMDataset")
    band = ET.SubElement(root, "PAMRasterBand", band="1")
    rat = ET.SubElement(band, "GDALRasterAttributeTable")
    
    # --- DEFINICIÓN DE COLUMNAS ---
    
    # Columna 0: Value (ID del píxel)
    fdef_val = ET.SubElement(rat, "FieldDefn", index="0")
    ET.SubElement(fdef_val, "Name").text = "Value"
    ET.SubElement(fdef_val, "Type").text = "0" # Integer
    ET.SubElement(fdef_val, "Usage").text = "0" # Generic
    
    # Columna 1: Class_Name (El Texto que quieres ver)
    fdef_txt = ET.SubElement(rat, "FieldDefn", index="1")
    ET.SubElement(fdef_txt, "Name").text = "Class_Name"
    ET.SubElement(fdef_txt, "Type").text = "2" # String
    
    # ### <--- CAMBIO CRÍTICO: Usage = 2 significa "Name" (Nombre de la clase)
    # Esto obliga a QGIS a usar este campo como etiqueta principal.
    ET.SubElement(fdef_txt, "Usage").text = "2" 

    # --- INSERCIÓN DE FILAS ---
    # Es VITAL que las filas estén ordenadas o coincidan con el índice si es posible
    # Para mayor seguridad, creamos un mapa sparse si faltan valores
    
    # Encontramos el valor máximo para saber cuántas filas declarar (GDAL a veces lo prefiere)
    # Pero para hacerlo simple, inyectamos solo las filas existentes.
    
    for i, (val, txt) in enumerate(rows_data):
        row = ET.SubElement(rat, "Row", index=str(i)) # Index relativo a la tabla
        ET.SubElement(row, "F").text = str(val)
        ET.SubElement(row, "F").text = str(txt)

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    try:
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"  ✅ PAM XML Generado (Usage=Name).")
        return True
    except Exception as e:
        print(f"  ❌ Error escribiendo XML: {e}")
        return False

def generate_qgis_style(raster_layer, output_folder):
    """Genera archivo de estilo .qml para QGIS."""
    
    if hasattr(raster_layer, "name"):
        layer_name = raster_layer.name
    else:
        layer_name = os.path.basename(str(raster_layer))
        
    safe_name = layer_name.replace(" ", "_").replace(".", "")
    qml_path = os.path.join(output_folder, f"{safe_name}.qml")

    print(f"--- 🎨 GENERANDO ESTILO QML ---")

    classification_data = []
    try:
        fields = [f.name for f in arcpy.ListFields(raster_layer)]
        text_field = next((f for f in fields if 'rang' in f.lower() or 'conc' in f.lower()), None)
        value_field = "Value"
        
        if not text_field:
            print("  ⚠️ No encuentro campo de texto para la leyenda.")
            return False

        with arcpy.da.SearchCursor(raster_layer, [value_field, text_field]) as cursor:
            for row in cursor:
                classification_data.append({"val": int(row[0]), "label": str(row[1])})
        classification_data.sort(key=lambda x: x['val'])
        
    except Exception as e:
        print(f"  ❌ Error leyendo tabla raster: {e}")
        return False

    # Interpolación de color (Azul -> Rojo)
    def interpolate_color(idx, total):
        if total <= 1: ratio = 0
        else: ratio = idx / (total - 1)
        r = int(255 * ratio)
        g = 0
        b = int(255 * (1 - ratio))
        return f"{r},{g},{b},255"

    # Construcción XML
    qml_content = [
        '<!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM">',
        '<qgis version="3.0.0" styleCategories="AllStyleCategories" minScale="1e+08" maxScale="0" hasScaleBasedVisibilityFlag="0">',
        '  <pipe>',
        '    <rasterrenderer opacity="1" alphaBand="-1" band="1" type="paletted">',
        '      <minMaxOrigin><limits>None</limits><extent>WholeRaster</extent></minMaxOrigin>',
        '      <colorPalette>'
    ]

    total = len(classification_data)
    for i, item in enumerate(classification_data):
        col = interpolate_color(i, total)
        hex_col = "#%02x%02x%02x" % tuple(map(int, col.split(',')[:3]))
        lbl = item['label'].replace("&", "&amp;").replace("<", "&lt;")
        qml_content.append(f'        <paletteEntry value="{item["val"]}" color="{hex_col}" alpha="255" label="{lbl}"/>')

    qml_content.extend(['      </colorPalette>', '    </rasterrenderer>', '  </pipe>', '</qgis>'])

    try:
        with open(qml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(qml_content))
        print(f"  ✅ QML Generado.")
        return True
    except Exception as e:
        print(f"  ❌ Error QML: {e}")
        return False

def export_project_layers_to_csv(aprx_path, output_folder, target_fields):
    """Exporta atributos a CSV y realiza ETL (parsing de rangos)."""
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    results = {'success': 0, 'errors': 0, 'details': []}

    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
    except Exception as e:
        raise Exception(f"Error APRX: {e}")

    for m in aprx.listMaps():
        for lyr in m.listLayers():
            if not (lyr.supports("DataSource") and (lyr.isRasterLayer or lyr.isFeatureLayer)):
                continue

            try:
                # 1. Asegurar Tabla
                if lyr.isRasterLayer and not getattr(arcpy.Describe(lyr), 'hasRAT', False):
                    try: arcpy.management.BuildRasterAttributeTable(lyr, "Overwrite")
                    except: pass

                # 2. Filtrar Campos
                try: all_fields = [f.name for f in arcpy.ListFields(lyr)]
                except: continue
                
                fields_to_read = [f for f in target_fields if f in all_fields]
                if not fields_to_read: continue

                range_col = next((f for f in fields_to_read if 'rang' in f.lower() or 'conc' in f.lower()), None)

                # 3. Exportar
                safe_name = lyr.name.replace(" ", "_").replace(".", "")
                csv_path = os.path.join(output_folder, f"{safe_name}.csv")
                
                header = list(fields_to_read)
                if range_col:
                    header.extend(['min_val', 'max_val', 'css_class'])

                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

                    with arcpy.da.SearchCursor(lyr, fields_to_read) as cursor:
                        for row in cursor:
                            data = list(row)
                            if range_col:
                                idx = fields_to_read.index(range_col)
                                # AQUÍ LLAMAMOS AL HELPER QUE FALTABA
                                min_v, max_v = _parse_range_text(row[idx])
                                try: css_class = f"cat_{int(row[0])}"
                                except: css_class = "cat_gen"
                                data.extend([min_v, max_v, css_class])
                            
                            writer.writerow([str(x).replace('\n', ' ') for x in data])

                results['success'] += 1
                results['details'].append(f"✅ {lyr.name}")

            except Exception as e:
                results['errors'] += 1
                results['details'].append(f"❌ {lyr.name}: {str(e)}")
    
    return results

# =============================================================================
# 🎯 MAIN ORCHESTRATOR (Para probarlo todo junto)
# =============================================================================

def process_full_stack(layer_obj, output_folder, aprx_path_for_csv):
    """
    Ejecuta TODO el flujo: COG + CSV + PAM + QML.
    """
    print(f"\n🚀 PROCESANDO FULL STACK: {layer_obj.name}")
    
    # 1. Generar Imagen (COG)
    cog_path = export_to_cog_arcpy(layer_obj, output_folder)
    
    if cog_path:
        # 2. Generar Datos (CSV)
        # Nota: Exportamos CSV del proyecto entero, pero filtramos por nombre si quieres
        export_project_layers_to_csv(aprx_path_for_csv, output_folder, ["Value", "rang_concentracio_al", "rang_concentració_al"])
        
        # Nombre esperado del CSV
        safe_name = layer_obj.name.replace(" ", "_").replace(".", "")
        csv_path = os.path.join(output_folder, f"{safe_name}.csv")
        
        # 3. Inyectar Metadatos (PAM)
        if os.path.exists(csv_path):
            generate_gdal_pam_xml(cog_path, csv_path)
        else:
            print("  ⚠️ No se encontró el CSV para inyectar PAM.")
            
        # 4. Generar Estilo (QML)
        generate_qgis_style(layer_obj, output_folder)

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Cambia esto por tus rutas reales
    aprx_path = r"C:\Users\becari.g.fernandez\Desktop\treballs\02_tif_to_cogeotiff\proyecto\tif_to_cogeotiff\tif_to_cogeotiff.aprx" 
    out_dir = r"C:\Temp\ArcGIS\Exportaciones"
    
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
        m = aprx.listMaps("Map")[0]
        
        for lyr in m.listLayers():
            if lyr.isRasterLayer:
                process_full_stack(lyr, out_dir, aprx_path)
                
    except Exception as e:
        print(f"Error Global: {e}")