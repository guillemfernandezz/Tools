# 1_stylx_utils.py
import sqlite3
import json
import os

def get_cims_from_stylx(style_path, verbose=True):
    all_symbol_cims = {}
    if verbose: print(f"Leyendo estilo: {style_path}")
    if not os.path.exists(style_path): return all_symbol_cims

    try:
        conn = sqlite3.connect(style_path)
        conn.text_factory = str
        cursor = conn.cursor()
        cursor.execute("SELECT ID, NAME, CONTENT FROM ITEMS")
        rows = cursor.fetchall()
        
        if verbose: print(f"Encontrados {len(rows)} items.")
        decoder = json.JSONDecoder()

        for row in rows:
            item_id, name, cim_json_string = row
            if cim_json_string and '"type":"CIM' in cim_json_string and 'Symbol"' in cim_json_string:
                try:
                    cim_data, _ = decoder.raw_decode(cim_json_string.strip())
                    all_symbol_cims[item_id] = {'name': name, 'cim_data': cim_data}
                except: pass
        conn.close()
    except Exception as e:
        print(f"Error SQLite: {e}")

    return all_symbol_cims

def actualizar_cims_en_stylx(style_path, cims_a_actualizar):
    conn = None
    try:
        conn = sqlite3.connect(style_path)
        cursor = conn.cursor()
        update_data = [] 
        for item_id, cim_data in cims_a_actualizar.items():
            json_string = json.dumps(cim_data, ensure_ascii=False)
            update_data.append((json_string, item_id))
        cursor.executemany("UPDATE ITEMS SET CONTENT = ? WHERE ID = ?", update_data)
        conn.commit()
        if conn: conn.close()
    except Exception as e:
        print(f"Error update: {e}")
        if conn: conn.close()
        raise