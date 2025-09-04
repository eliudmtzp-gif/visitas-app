import csv
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def limpiar_fecha(valor):
    valor = valor.strip()
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    print(f"⚠️ Fecha inválida detectada: '{valor}' → se insertará como NULL.")
    return None

def actualizar_o_insertar(ruta_csv):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    with open(ruta_csv, newline='', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)

        # Eliminar BOM si existe en la primera columna
        if lector.fieldnames[0].startswith('\ufeff'):
            lector.fieldnames[0] = lector.fieldnames[0].replace('\ufeff', '')

        for fila in lector:
            identificador = fila['Id'].strip().upper()
            fecha = limpiar_fecha(fila['FECHA'])
            entrego = fecha  # Se usa como copia de FECHA

            cur.execute("""
                INSERT INTO visitas (
                    identificador, nombre, direccion, telefono,
                    variante, entrego, actualmente_la_visita,
                    observaciones, fecha, ver_en_maps
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (identificador)
                DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    direccion = EXCLUDED.direccion,
                    telefono = EXCLUDED.telefono,
                    variante = EXCLUDED.variante,
                    entrego = EXCLUDED.entrego,
                    actualmente_la_visita = EXCLUDED.actualmente_la_visita,
                    observaciones = EXCLUDED.observaciones,
                    fecha = EXCLUDED.fecha,
                    ver_en_maps = EXCLUDED.ver_en_maps;
            """, (
                identificador,
                fila['NOMBRE'].strip(),
                fila['DIRECCIÓN'].strip(),
                fila['TELÉFONO'].strip(),
                fila['VARIANTE'].strip(),
                entrego,
                fila['ACTUALMENTE LA VISITA'].strip(),
                fila['OBSERVACIONES'].strip(),
                fecha,
                fila['VER EN MAPS'].strip()
            ))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Migración completa: registros agregados o actualizados.")

# Ejecuta esto cuando quieras sincronizar sin borrar
actualizar_o_insertar("db.csv")