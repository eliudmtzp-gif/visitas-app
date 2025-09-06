from flask import Flask, render_template, request, redirect
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL no está definido. Verifica tus variables de entorno.")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

app = Flask(__name__)

def crear_tabla_si_no_existe():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitas (
            id SERIAL PRIMARY KEY,
            identificador VARCHAR(10) UNIQUE,
            nombre VARCHAR(100),
            direccion TEXT,
            telefono VARCHAR(50),
            variante VARCHAR(50),
            entrego DATE,
            actualmente_la_visita TEXT,
            observaciones TEXT,
            fecha DATE,
            ver_en_maps TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def cargar_db(grupo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT identificador, nombre, direccion, telefono,
               variante, entrego, actualmente_la_visita,
               observaciones, fecha, ver_en_maps
        FROM visitas
        WHERE LEFT(identificador, 2) = %s;
    """, (grupo,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columnas = [
    "identificador", "nombre", "direccion", "telefono",
    "variante", "entrego", "actualmente_la_visita",
    "observaciones", "fecha", "ver_en_maps"
    ]
    return [dict(zip(columnas, row)) for row in rows]

@app.route('/')
def index():
    grupo = request.args.get('grupo', 'QA')
    personas = cargar_db(grupo)
    print("👀 Registros cargados:", personas)
    return render_template('index.html', personas=personas, grupo=grupo)

@app.route('/actualizar', methods=['POST'])
def actualizar():
    identificador = request.form['identificador']
    nueva_obs = request.form['observacion']
    nueva_fecha = request.form['fecha']
    grupo = request.form['grupo']

    # Validación: si no hay fecha, no actualices
    if not nueva_fecha:
        mensaje = f"⚠️ Por favor, agrega una fecha antes de actualizar el registro {identificador}"
        return redirect(f"/?grupo={grupo}&mensaje={mensaje}&resaltado={identificador}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE visitas
        SET observaciones = %s,
            fecha = %s
        WHERE identificador = %s;
    """, (nueva_obs, nueva_fecha, identificador))
    filas_afectadas = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if filas_afectadas > 0:
        mensaje = f"✅ Registro {identificador} actualizado correctamente"
    else:
        mensaje = f"⚠️ No se encontró el registro {identificador}"

    return redirect(f"/?grupo={grupo}&mensaje={mensaje}&resaltado={identificador}")

if __name__ == '__main__':
    crear_tabla_si_no_existe()

    # Si quieres migrar automáticamente al iniciar la app, descomenta esta línea:
    # import borrar_todo_y_migrar  # Asegúrate que este script no se ejecute al importar

    app.run(debug=True)