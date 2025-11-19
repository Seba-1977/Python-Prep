import csv
import re
from datetime import datetime

# ============================================================
# PARSEADOR UNIVERSAL DE FECHAS
# ============================================================

MESES_ES = {
    "enero":1, "ene":1,
    "febrero":2, "feb":2,
    "marzo":3, "mar":3,
    "abril":4, "abr":4,
    "mayo":5,
    "junio":6, "jun":6,
    "julio":7, "jul":7,
    "agosto":8, "ago":8,
    "septiembre":9, "setiembre":9, "sep":9, "set":9,
    "octubre":10, "oct":10,
    "noviembre":11, "nov":11,
    "diciembre":12, "dic":12
}

def parse_fecha_universal(texto):
    if texto is None:
        return None

    t = str(texto).strip().lower()
    t = re.sub(r"\b(hs|hrs|hr|h)\.?$", "", t).strip()
    t = t.replace(",", " ").replace("  ", " ")

    # ISO
    try:
        return datetime.fromisoformat(t)
    except:
        pass

    # Ej: 17 de noviembre de 2025 08:23
    patron = r"(\d{1,2})\s*(de)?\s*([a-záéíóú]+)\s*(de)?\s*(\d{2,4})(?:\s+(\d{1,2}:\d{2}))?"
    m = re.search(patron, t)
    if m:
        dia = int(m.group(1))
        mes_txt = m.group(3)
        anio = int(m.group(5))
        hora = m.group(6)
        mes = MESES_ES.get(mes_txt[:3], MESES_ES.get(mes_txt))
        
        if mes is None:
            return None
        if anio < 100:
            anio += 2000
        
        if hora:
            return datetime.strptime(f"{dia}/{mes}/{anio} {hora}", "%d/%m/%Y %H:%M")
        return datetime.strptime(f"{dia}/{mes}/{anio}", "%d/%m/%Y")

    # Numéricos
    patron_num = r"(\d{1,4})[\/\-.](\d{1,2})[\/\-.](\d{1,4})(?:\s+(\d{1,2}:\d{2}))?"
    m = re.search(patron_num, t)
    if m:
        a, b, c = m.group(1), m.group(2), m.group(3)
        hora = m.group(4)
        nums = list(map(int, [a, b, c]))

        if nums[0] > 31:
            anio, mes, dia = nums
        elif nums[2] > 31:
            dia, mes, anio = nums
        else:
            dia, mes, anio = nums
            if anio < 100:
                anio += 2000

        if hora:
            return datetime.strptime(f"{dia}/{mes}/{anio} {hora}", "%d/%m/%Y %H:%M")
        return datetime.strptime(f"{dia}/{mes}/{anio}", "%d/%m/%Y")

    return None


# ============================================================
# CARGA DE ARCHIVOS CSV (SIN PANDAS)
# ============================================================

def cargar_csv(archivo):
    datos = []
    with open(archivo, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fila = {k.lower(): v for k, v in row.items()}
            datos.append(fila)
    return datos


# ============================================================
# UNIFICAR DATOS
# ============================================================

def procesar_datos(mercado, afip):
    unificados = []

    for r in mercado:
        unificados.append({
            "fecha": parse_fecha_universal(r["fecha"]),
            "numero_factura": r.get("numero_factura", ""),
            "dni": r["dni"],
            "provincia": r["provincia"],
            "valor_total": float(r["valor_total"])
        })

    for r in afip:
        unificados.append({
            "fecha": parse_fecha_universal(r["fecha"]),
            "numero_factura": r["numero_factura"],
            "dni": r["dni"],
            "provincia": r.get("provincia", "cordoba"),
            "valor_total": float(r["valor_total"])
        })

    return unificados


# ============================================================
# FILTROS
# ============================================================

def filtrar_fecha(datos, desde, hasta):
    d = parse_fecha_universal(desde)
    h = parse_fecha_universal(hasta)
    return [r for r in datos if r["fecha"] and d <= r["fecha"] <= h]

def filtrar_provincia(datos, prov):
    return [r for r in datos if r["provincia"].lower() == prov.lower()]


# ============================================================
# MENÚ SIN TKINTER
# ============================================================

def menu():
    print("\n===== SISTEMA DE FACTURAS =====")
    print("1) Filtrar por fecha y provincia")
    print("2) Vista previa")
    print("3) Salir")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

mercado = cargar_csv("lista_mercadolibre.csv")
afip = cargar_csv("lista_afip.csv")

datos = procesar_datos(mercado, afip)
datos_filtrados = datos[:]  # copia inicial

while True:
    menu()
    op = input("\nOpción: ")

    if op == "1":
        print("\n--- FILTRO DE FECHAS ---")
        desde = input("Fecha DESDE: ")
        hasta = input("Fecha HASTA: ")

        datos_filtrados = filtrar_fecha(datos, desde, hasta)

        print("\n--- PROVINCIA ---")
        prov = input("Provincia (Enter = Córdoba): ")
        if prov.strip() == "":
            prov = "cordoba"

        datos_filtrados = filtrar_provincia(datos_filtrados, prov)
        print("\n✔ Filtros aplicados correctamente.")

    elif op == "2":
        print("\n===== VISTA PREVIA =====")
        for r in datos_filtrados[:20]:
            print(r)
        print("\n(Mostrando primeros 20 registros)")

    elif op == "3":
        print("Saliendo...")
        break

    else:
        print("Opción inválida.")
