import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import pdfplumber
import os

# ----------------------------------------------------
# Funcion que abre un cuadro para seleccionar un archivo
# ----------------------------------------------------
def seleccionar_archivo(titulo, tipos):
    root = tk.Tk()
    root.withdraw()
    archivo = filedialog.askopenfilename(title=titulo, filetypes=tipos)
    if not archivo:
        messagebox.showerror("Error", "No seleccionaste ningún archivo.")
        exit()
    return archivo

# ----------------------------------------------------
# Selección interactiva de archivos
# ----------------------------------------------------
messagebox.showinfo("Iniciar", "Vas a seleccionar:\n1) PDF del banco\n2) Archivo de reglas\n3) Dónde guardar el archivo final")

pdf_path = seleccionar_archivo("Seleccionar PDF del banco", [("PDF", "*.pdf")])
rules_path = seleccionar_archivo("Seleccionar archivo de reglas", [("Excel", "*.xlsx"), ("CSV", "*.csv")])

# Seleccionar archivo de salida
root = tk.Tk()
root.withdraw()
out_path = filedialog.asksaveasfilename(
    title="Guardar resultado como...",
    defaultextension=".xlsx",
    filetypes=[("Excel", "*.xlsx")]
)
if not out_path:
    messagebox.showerror("Error", "No elegiste archivo de salida.")
    exit()

# ----------------------------------------------------
# Cargar reglas
# ----------------------------------------------------
if rules_path.endswith(".csv"):
    rules = pd.read_csv(rules_path)
else:
    rules = pd.read_excel(rules_path)

# Convertimos reglas a minúsculas
rules["texto"] = rules["texto"].str.lower()
rules["clasificacion"] = rules["clasificacion"].str.strip()

# ----------------------------------------------------
# Leer texto del PDF
# ----------------------------------------------------
texto_pdf = ""
with pdfplumber.open(pdf_path) as pdf:
    for pag in pdf.pages:
        texto_pdf += pag.extract_text() + "\n"

texto_pdf = texto_pdf.lower()

# ----------------------------------------------------
# Aplicar clasificación
# ----------------------------------------------------
resultados = []
for _, fila in rules.iterrows():
    if fila["texto"] in texto_pdf:
        resultados.append({
            "texto_encontrado": fila["texto"],
            "clasificacion": fila["clasificacion"]
        })

df_resultados = pd.DataFrame(resultados)

# ----------------------------------------------------
# Guardar archivo de salida
# ----------------------------------------------------
df_resultados.to_excel(out_path, index=False)

messagebox.showinfo("Listo", f"Clasificación generada correctamente.\nArchivo guardado en:\n{out_path}")
