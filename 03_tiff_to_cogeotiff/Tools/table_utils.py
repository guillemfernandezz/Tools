# table_utils.py
import arcpy
import csv
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from typing import List

# ==========================================
# 🧠 BACKEND: LÓGICA DE PROCESAMIENTO (ETL)
# ==========================================

def _parse_range_text(text):
    """(Helper Privado) Parsea texto de rangos a float."""
    if not text: return 0.0, 0.0
    clean_txt = str(text).lower().replace(',', '.')
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", clean_txt)]
    
    if not nums: return 0.0, 0.0

    if any(x in clean_txt for x in ['menys', 'menos', '<']):
        return 0.0, nums[0]
    elif any(x in clean_txt for x in ['entre', '-']):
        return (nums[0], nums[1]) if len(nums) >= 2 else (nums[0], nums[0])
    elif any(x in clean_txt for x in ['més', 'mas', '>', 'igual']):
        return nums[0], 999.9 
    
    return nums[0], nums[0]

def export_project_layers_to_csv(aprx_path: str, output_folder: str, target_fields: List[str]) -> dict:
    """Función principal de exportación y limpieza."""
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except OSError as e:
            raise OSError(f"No se pudo crear la carpeta: {e}")

    results = {'success': 0, 'errors': 0, 'details': []}

    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
    except Exception as e:
        raise Exception(f"Error cargando APRX: {e}")

    for m in aprx.listMaps():
        for lyr in m.listLayers():
            if not (lyr.supports("DataSource") and (lyr.isRasterLayer or lyr.isFeatureLayer)):
                continue

            try:
                # Gestión resiliente de RAT
                if lyr.isRasterLayer and not getattr(arcpy.Describe(lyr), 'hasRAT', False):
                    try: arcpy.management.BuildRasterAttributeTable(lyr, "Overwrite")
                    except: pass

                # Validar campos
                try: all_fields = [f.name for f in arcpy.ListFields(lyr)]
                except: continue
                
                fields_to_read = [f for f in target_fields if f in all_fields]
                if not fields_to_read: continue

                # Auto-detección de columnas de rango
                range_col = next((f for f in fields_to_read if 'rang' in f.lower() or 'conc' in f.lower()), None)

                # Setup CSV
                safe_name = lyr.name.replace(" ", "_").replace(".", "")
                csv_path = os.path.join(output_folder, f"{safe_name}.csv")
                header = list(fields_to_read)
                if range_col:
                    header.extend(['min_val', 'max_val', 'css_class'])

                # Escritura
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

                    with arcpy.da.SearchCursor(lyr, fields_to_read) as cursor:
                        for row in cursor:
                            data = list(row)
                            if range_col:
                                idx = fields_to_read.index(range_col)
                                min_v, max_v = _parse_range_text(row[idx])
                                # Lógica de clase CSS basada en Value (si existe y es int)
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

# ==========================================
# 🖥️ FRONTEND: INTERFAZ GRÁFICA (Tkinter)
# ==========================================

class _TableUtilsGUI:
    """Clase interna para la GUI. No debe ser llamada desde fuera idealmente."""
    def __init__(self, root):
        self.root = root
        self.root.title("Table Utils | ArcGIS Pro Library")
        self.root.geometry("550x450")
        
        # UI Styling simple
        bg_color = "#f5f5f5"
        self.root.configure(bg=bg_color)
        
        tk.Label(root, text="Exportador de Tablas & ETL", bg=bg_color, font=("Arial", 12, "bold")).pack(pady=10)

        # Frame inputs
        frm = tk.Frame(root, bg=bg_color, padx=10)
        frm.pack(fill="x")

        # Inputs
        self._make_input(frm, "Proyecto (.aprx):", 0, self.browse_aprx)
        self._make_input(frm, "Salida:", 1, self.browse_out)
        
        tk.Label(frm, text="Campos:", bg=bg_color).grid(row=2, column=0, sticky="w")
        self.ent_fields = tk.Entry(frm, width=40)
        self.ent_fields.insert(0, "Value, Count, rang_concentració_al, Area")
        self.ent_fields.grid(row=2, column=1, pady=5)

        # Botón
        tk.Button(root, text="Ejecutar Proceso", bg="#007acc", fg="white", 
                  command=self.run).pack(pady=15)

        # Log
        self.log_widget = scrolledtext.ScrolledText(root, height=10)
        self.log_widget.pack(padx=10, pady=5, fill="both", expand=True)

    def _make_input(self, parent, label, row, cmd):
        tk.Label(parent, text=label, bg="#f5f5f5").grid(row=row, column=0, sticky="w")
        ent = tk.Entry(parent, width=40)
        ent.grid(row=row, column=1, pady=5)
        tk.Button(parent, text="...", command=lambda: cmd(ent)).grid(row=row, column=2, padx=5)
        if row == 0: self.ent_aprx = ent
        if row == 1: self.ent_out = ent

    def browse_aprx(self, ent):
        f = filedialog.askopenfilename(filetypes=[("ArcGIS Project", "*.aprx")])
        if f: ent.delete(0, tk.END); ent.insert(0, f)

    def browse_out(self, ent):
        d = filedialog.askdirectory()
        if d: ent.delete(0, tk.END); ent.insert(0, d)

    def log(self, text):
        self.log_widget.insert(tk.END, text + "\n")
        self.log_widget.see(tk.END)
        self.root.update()

    def run(self):
        aprx = self.ent_aprx.get()
        out = self.ent_out.get()
        flds = [f.strip() for f in self.ent_fields.get().split(',')]
        
        if not aprx or not out:
            messagebox.showwarning("Faltan datos", "Rellena las rutas.")
            return
            
        self.log(">>> Iniciando...")
        try:
            # Llamada interna a la función del mismo módulo
            res = export_project_layers_to_csv(aprx, out, flds)
            for d in res['details']: self.log(d)
            self.log(f">>> Fin. Éxitos: {res['success']}")
            messagebox.showinfo("Éxito", "Exportación finalizada.")
        except Exception as e:
            self.log(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

def launch_gui():
    """Lanza la interfaz gráfica de la librería."""
    root = tk.Tk()
    _TableUtilsGUI(root)
    root.mainloop()

# ==========================================
# 🚀 PUNTO DE ENTRADA (Main Guard)
# ==========================================
if __name__ == "__main__":
    # Esto solo se ejecuta si lanzas el script directamente, 
    # NO cuando lo importas desde otro lado.
    print("Iniciando modo GUI...")
    launch_gui()