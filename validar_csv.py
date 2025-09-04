import csv
import os
from datetime import datetime

def limpiar_fecha(valor):
    valor = valor.strip()
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    return None

def validar_csv(ruta_csv):
    columnas_requeridas = ["Id", "NOMBRE", "FECHA", "OBSERVACIONES", "VARIANTE"]
    errores = 0

    if not os.path.exists(ruta_csv):
        print(f"❌ El archivo '{ruta_csv}' no existe.")
        return False

    with open(ruta_csv, newline='', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)

        # Eliminar BOM si existe en la primera columna
        if lector.fieldnames[0].startswith('\ufeff'):
            lector.fieldnames[0] = lector.fieldnames[0].replace('\ufeff', '')

        # Verificar que las columnas requeridas estén presentes (sin importar el orden)
        faltantes = [col for col in columnas_requeridas if col not in lector.fieldnames]
        if faltantes:
            print(f"❌ Faltan columnas requeridas: {faltantes}")
            print(f"📄 Columnas encontradas: {lector.fieldnames}")
            return False

        identificadores = set()

        for i, fila in enumerate(lector, start=1):
            id_ = fila.get("Id", "").strip()
            nombre = fila.get("NOMBRE", "").strip()
            fecha_raw = fila.get("FECHA", "").strip()
            variante = fila.get("VARIANTE", "").strip()

            # Validar duplicados
            if id_ in identificadores:
                print(f"⚠️ Fila {i}: identificador duplicado '{id_}'.")
                errores += 1
            else:
                identificadores.add(id_)

            # Validar formato de fecha si existe
            if fecha_raw:
                fecha = limpiar_fecha(fecha_raw)
                if not fecha:
                    print(f"⚠️ Fila {i}: fecha inválida '{fecha_raw}'. Se ignorará en migración.")
            else:
                print(f"ℹ️ Fila {i}: fecha vacía. Se insertará como NULL.")

        if errores == 0:
            print("✅ El archivo está bien formateado y listo para migrar.")
            return True
        else:
            print(f"❌ Se encontraron {errores} errores críticos. Corrige antes de migrar.")
            return False

# Ejecuta esto desde consola
validar_csv("db.csv")