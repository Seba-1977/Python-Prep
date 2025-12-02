#!/usr/bin/env python3
"""
clasificador_por_excel.py

Uso:
    python clasificador_por_excel.py --rules reglas.xlsx --pdf extracto.pdf --out salida.xlsx

Descripción:
    - Carga un archivo Excel/CSV con 2 columnas: "CLASIFICACION CONTABLE" y "ORIGINAL S/BANCO".
    - Lee el PDF, extrae texto (PyPDF2) por página y por línea.
    - Para cada línea, busca si alguna "ORIGINAL S/BANCO" aparece (case-insensitive, substring).
    - Si hay match, escribe la categoría; si no, "SIN CLASIFICAR".
    - Exporta un Excel con: pagina, linea_texto, categoria_detectada, patron_detectado.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import PyPDF2
import logging

# ------- Config logging -------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------- Funciones -------

def cargar_reglas(path):
    """
    Carga reglas desde Excel (hoja 0) o CSV.
    Espera columnas: 'CLASIFICACION CONTABLE' y 'ORIGINAL S/BANCO' (no case-sensitive).
    Devuelve lista de tuplas (categoria, patron) ordenadas.
    Si una celda de patron tiene múltiples patrones, se puede separar por ';' (opcional).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo de reglas no encontrado: {path}")

    if p.suffix.lower() in [".xls", ".xlsx"]:
        df = pd.read_excel(p, dtype=str, sheet_name=0)
    else:
        # csv
        df = pd.read_csv(p, dtype=str)

    # Normalizar nombres de columnas
    cols = {c.strip().upper(): c for c in df.columns}
    # Buscar columnas
    try:
        cat_col = cols["CLASIFICACION CONTABLE"]
        pat_col = cols["ORIGINAL S/BANCO"]
    except KeyError as e:
        raise KeyError("El archivo de reglas debe tener las columnas EXACTAS: "
                       "'CLASIFICACION CONTABLE' y 'ORIGINAL S/BANCO'") from e

    reglas = []
    for _, row in df.iterrows():
        categoria = str(row[cat_col]).strip() if pd.notna(row[cat_col]) else ""
        patrones_raw = str(row[pat_col]).strip() if pd.notna(row[pat_col]) else ""
        if not categoria:
            continue
        if patrones_raw == "" or patrones_raw.lower() in ["nan", "none"]:
            # si no hay patrón, se saltea (podés querer mantener categorías vacías)
            continue

        # soporta múltiples patrones en una celda separados por ';'
        patrones = [p.strip() for p in patrones_raw.split(";") if p.strip()]
        for p in patrones:
            reglas.append((categoria, p))

    # ordenamos por longitud patrón descendente para evitar matches muy genéricos antes que específicos
    reglas.sort(key=lambda x: len(x[1]), reverse=True)
    logging.info(f"Cargadas {len(reglas)} reglas desde {p}")
    return reglas


def extraer_texto_pdf(path):
    """
    Extrae texto del PDF por página usando PyPDF2.
    Devuelve lista de (numero_pagina (1-based), texto_de_pagina).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"PDF no encontrado: {path}")

    textos = []
    with open(p, "rb") as f:
        lector = PyPDF2.PdfReader(f)
        num = len(lector.pages)
        logging.info(f"PDF abierto. Páginas: {num}")
        for i, pagina in enumerate(lector.pages):
            try:
                texto = pagina.extract_text() or ""
            except Exception as e:
                logging.warning(f"Error extrayendo texto en página {i+1}: {e}")
                texto = ""
            textos.append((i + 1, texto))
    return textos


def limpiar_linea(s):
    """
    Normaliza espacios y bordes.
    """
    return " ".join(s.split()).strip()


def clasificar_lineas_texto(texto_por_pagina, reglas):
    """
    Para cada línea encontrada en cada página, busca el primer patrón que coincida.
    Devuelve lista de dicts con keys: pagina, linea, categoria, patron.
    """
    resultados = []
    for pagina_num, texto in texto_por_pagina:
        if not texto:
            continue
        # separo por saltos de linea porque los extractors suelen devolver saltos
        for raw_line in texto.splitlines():
            linea = limpiar_linea(raw_line)
            if not linea:
                continue
            linea_up = linea.upper()
            encontrado = False
            for categoria, patron in reglas:
                if patron.upper() in linea_up:
                    resultados.append({
                        "pagina": pagina_num,
                        "linea_texto": linea,
                        "categoria_detectada": categoria,
                        "patron_detectado": patron
                    })
                    encontrado = True
                    break
            if not encontrado:
                resultados.append({
                    "pagina": pagina_num,
                    "linea_texto": linea,
                    "categoria_detectada": "SIN CLASIFICAR",
                    "patron_detectado": ""
                })
    return resultados


def exportar_resultados(resultados, salida_path):
    df = pd.DataFrame(resultados, columns=["pagina", "linea_texto", "categoria_detectada", "patron_detectado"])
    # Guardar Excel
    salida_p = Path(salida_path)
    df.to_excel(salida_p, index=False)
    logging.info(f"Exportado Excel con {len(df)} registros a: {salida_p}")


# ------- Main CLI -------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Clasificar movimientos de PDF usando reglas desde Excel/CSV.")
    parser.add_argument("--rules", "-r", required=True, help="Archivo Excel (.xlsx/.xls) o CSV con las reglas.")
    parser.add_argument("--pdf", "-p", required=True, help="Archivo PDF a clasificar.")
    parser.add_argument("--out", "-o", default="salida_clasificada.xlsx", help="Archivo Excel de salida.")
    args = parser.parse_args(argv)

    try:
        reglas = cargar_reglas(args.rules)
        texto_paginas = extraer_texto_pdf(args.pdf)
        resultados = clasificar_lineas_texto(texto_paginas, reglas)
        exportar_resultados(resultados, args.out)
        logging.info("Proceso finalizado correctamente.")
    except Exception as e:
        logging.exception("Error durante el proceso:")
        sys.exit(1)


if __name__ == "__main__":
    main()
