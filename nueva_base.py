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

def crear_usuario_admin(cur):
    # ✅ Crear tabla de usuarios si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE,
            clave TEXT
        )
    """)
    # ✅ Insertar usuario LaEra con contraseña 8824 si no existe
    cur.execute("""
        INSERT INTO usuarios (usuario, clave)
        VALUES ('LaEra', '8824')
        ON CONFLICT (usuario) DO NOTHING
    """)

def borrar_todo_y_migrar(ruta_csv):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ✅ Crear tabla visitas si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitas (
            identificador TEXT PRIMARY KEY,
            nombre TEXT,
            direccion TEXT,
            telefono TEXT,
            variante TEXT,
            entrego DATE,
            actualmente_la_visita TEXT,
            observaciones TEXT,
            fecha DATE,
            ver_en_maps TEXT
        )
    """)

    # Borra todos los registros existentes
    cur.execute("DELETE FROM visitas")

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

    # ✅ Crear usuario admin automáticamente
    crear_usuario_admin(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Migración completa: tabla visitas cargada y usuario LaEra creado/asegurado.")

# Ejecuta la migración
borrar_todo_y_migrar("db.csv")
