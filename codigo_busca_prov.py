import csv
from datetime import datetime
import os


# ---------------------------------------------------------
# PARSEAR FECHAS
# ---------------------------------------------------------
def parsear_fecha(fecha_str):
    fecha_str = fecha_str.strip()

    # Formato corto: 14/1/2025
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except:
        pass

    # Formato largo: 17 de noviembre de 2025 08:23 hs.
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    try:
        partes = fecha_str.lower().replace("hs.", "").replace("hs", "").split()
        dia = int(partes[0])
        mes = meses[partes[2]]
        anio = partes[4]
        return datetime.strptime(f"{dia}/{mes}/{anio}", "%d/%m/%Y")
    except:
        return None


# ---------------------------------------------------------
# LECTURA CSV (CON o SIN ENCABEZADO)
# ---------------------------------------------------------
def leer_csv(path, campos):
    datos = []

    try:
        with open(path, encoding="latin1") as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]

        if not lineas:
            print(f"Archivo vacío: {path}")
            return []

        primera_linea = lineas[0].lower()

        # Detectar si tiene encabezado
        tiene_header = all(c in primera_linea for c in ["fecha"])

        if tiene_header:
            reader = csv.DictReader(lineas, delimiter=";")
            for row in reader:
                fila = {c: row.get(c, "").strip() for c in campos}
                datos.append(fila)
        else:
            # No tiene encabezado → asignamos manualmente
            for linea in lineas:
                partes = linea.split(";")
                if len(partes) < len(campos):
                    continue
                fila = {campos[i]: partes[i].strip() for i in range(len(campos))}
                datos.append(fila)

        return datos

    except Exception as e:
        print(f"ERROR leyendo {path}: {e}")
        return []


# ---------------------------------------------------------
# NORMALIZAR AFIP
# ---------------------------------------------------------
def normalizar_afip(row):
    fecha = parsear_fecha(row["fecha"])
    if fecha is None:
        return None

    dni = row["dni"].strip()
    nro = row["numero_factura"].strip()

    monto = row["valor_total"].replace(",", ".")
    try:
        monto = float(monto)
    except:
        return None

    return {
        "fecha": fecha,
        "dni": dni if dni else None,
        "numero": nro,
        "valor": monto,
        "provincia": None
    }


# ---------------------------------------------------------
# NORMALIZAR MERCADOLIBRE
# ---------------------------------------------------------
def normalizar_mercado(row):
    dni = row["dni"].strip()
    if dni == "":
        return None

    provincia = row["provincia"].encode("latin1").decode("utf-8", errors="ignore").strip()

    return {
        "dni": dni,
        "provincia": provincia
    }


# ---------------------------------------------------------
# CARGA COMPLETA
# ---------------------------------------------------------
def cargar_todo():
    print("\n--- CARGAR ARCHIVOS ---")

    afip_path = input("Archivo AFIP: ").strip()
    mercado_path = input("Archivo MercadoLibre: ").strip()

    if not os.path.isfile(afip_path) or not os.path.isfile(mercado_path):
        print("Uno o ambos archivos no existen.")
        return []

    # Leer AFIP
    afip_raw = leer_csv(afip_path, ["fecha", "numero_factura", "dni", "valor_total"])
    afip = [f for r in afip_raw if (f := normalizar_afip(r))]

    # Leer MercadoLibre
    ml_raw = leer_csv(mercado_path, ["fecha", "valor_total", "dni", "provincia"])

    ml_provincias = {}
    for r in ml_raw:
        f = normalizar_mercado(r)
        if f:
            ml_provincias[f["dni"]] = f["provincia"]  # ÚLTIMA aparición del DNI gana

    # Asignar provincia desde MercadoLibre
    for f in afip:
        dni = f["dni"]
        if dni in ml_provincias:
            f["provincia"] = ml_provincias[dni]
        else:
            f["provincia"] = "Córdoba"   # ← NUEVA REGLA

    return afip


# ---------------------------------------------------------
# MOSTRAR LISTA
# ---------------------------------------------------------
def mostrar_resultados(datos):
    print("\n--- FACTURAS OBTENIDAS ---\n")
    for f in datos:
        print(
            f"{f['fecha'].strftime('%d/%m/%Y')}  |  "
            f"N° {f['numero']}  |  "
            f"{f['provincia']}  |  "
            f"${f['valor']:,.2f}"
        )
    print()


# ---------------------------------------------------------
# FILTRO POR PROVINCIA
# ---------------------------------------------------------
def filtrar_por_provincia(datos):
    prov = input("Provincia a filtrar: ").strip().lower()
    filtrado = [f for f in datos if f["provincia"].lower() == prov]
    return filtrado


# ---------------------------------------------------------
# FILTRO POR FECHA
# ---------------------------------------------------------
def filtrar_por_fecha(datos):
    f1 = input("Fecha desde (dd/mm/aaaa): ").strip()
    f2 = input("Fecha hasta (dd/mm/aaaa): ").strip()

    try:
        d1 = datetime.strptime(f1, "%d/%m/%Y")
        d2 = datetime.strptime(f2, "%d/%m/%Y")
    except:
        print("Fechas inválidas.")
        return []

    return [f for f in datos if d1 <= f["fecha"] <= d2]


# ---------------------------------------------------------
# EXPORTAR CSV
# ---------------------------------------------------------
def exportar_csv(datos):
    nombre = input("Nombre del archivo CSV de salida: ").strip()
    if not nombre.endswith(".csv"):
        nombre += ".csv"

    with open(nombre, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["fecha", "numero", "provincia", "valor"])

        for d in datos:
            writer.writerow([
                d["fecha"].strftime("%d/%m/%Y"),
                d["numero"],
                d["provincia"],
                f"{d['valor']:.2f}"
            ])

    print(f"\nArchivo generado: {nombre}\n")


# ---------------------------------------------------------
# MENÚ
# ---------------------------------------------------------
def menu():
    datos = []

    while True:
        print("\n--- SISTEMA FACTURAS ---")
        print("1. Cargar archivos")
        print("2. Mostrar facturas procesadas")
        print("3. Filtrar por provincia")
        print("4. Filtrar por fecha")
        print("5. Exportar resultados a CSV")
        print("6. Salir")

        op = input("Opción: ").strip()

        if op == "1":
            datos = cargar_todo()
            print(f"\nCargados {len(datos)} registros.\n")

        elif op == "2":
            if datos:
                mostrar_resultados(datos)
            else:
                print("Primero cargue los archivos.")

        elif op == "3":
            if datos:
                mostrar_resultados(filtrar_por_provincia(datos))
            else:
                print("Primero cargue los archivos.")

        elif op == "4":
            if datos:
                mostrar_resultados(filtrar_por_fecha(datos))
            else:
                print("Primero cargue los archivos.")

        elif op == "5":
            if datos:
                exportar_csv(datos)
            else:
                print("No hay datos para exportar.")

        elif op == "6":
            break
        else:
            print("Opción inválida.")


# ---------------------------------------------------------
# EJECUTAR
# ---------------------------------------------------------
menu()

