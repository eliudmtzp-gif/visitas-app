from flask import Flask, render_template, request, redirect, flash, session
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
app.secret_key = "clave-secreta"  # Necesario para sesiones y flash

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
        WHERE LEFT(identificador, 2) = %s
        ORDER BY identificador ASC;
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
    resaltado = request.args.get('resaltado', '')
    rol = session.get('rol', 'visitante')  # 👈 rol por defecto visitante
    personas = cargar_db(grupo)
    return render_template('index.html',
                           personas=personas,
                           grupo=grupo,
                           rol=rol,
                           resaltado=resaltado)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        # 👇 Aquí defines tus credenciales de admin
        if usuario == "LaEra" and clave == "8824":
            session['rol'] = 'admin'
            flash("✅ Has ingresado como administrador")
            return redirect('/')
        else:
            flash("⚠️ Credenciales incorrectas")
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('rol', None)
    flash("Has salido del modo administrador")
    return redirect('/')

@app.route('/actualizar', methods=['POST'])
def actualizar():
    identificador = request.form['identificador']
    nueva_obs = request.form['observacion']
    nueva_fecha = request.form['fecha']
    grupo = request.form['grupo']

    if not nueva_fecha:
        flash(f"⚠️ Por favor, agrega una fecha antes de actualizar el registro {identificador}")
        return redirect(f"/?grupo={grupo}&resaltado={identificador}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE visitas
        SET observaciones = COALESCE(observaciones, '') || 
                            CASE WHEN %s <> '' THEN E'\n- ' || %s ELSE '' END,
            fecha = %s
        WHERE identificador = %s;
    """, (nueva_obs, nueva_obs, nueva_fecha, identificador))
    filas_afectadas = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if filas_afectadas > 0:
        flash(f"✅ Registro {identificador} actualizado correctamente")
    else:
        flash(f"⚠️ No se encontró el registro {identificador}")

    return redirect(f"/?grupo={grupo}&resaltado={identificador}")

@app.route('/nuevo', methods=['POST'])
def nuevo():
    identificador = request.form['identificador']
    nombre = request.form['nombre']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    variante = request.form['variante']
    actualmente = request.form['actualmente_la_visita']
    observaciones = request.form['observaciones']
    fecha = request.form['fecha']
    ver_en_maps = request.form['ver_en_maps']
    grupo = request.form['grupo']

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO visitas (identificador, nombre, direccion, telefono,
                                 variante, actualmente_la_visita, observaciones,
                                 fecha, ver_en_maps)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (identificador, nombre, direccion, telefono,
              variante, actualmente, observaciones, fecha, ver_en_maps))
        conn.commit()
        flash(f"✅ Nuevo registro {identificador} agregado correctamente")
    except Exception as e:
        conn.rollback()
        flash(f"⚠️ Error al agregar el registro: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(f"/?grupo={grupo}&resaltado={identificador}")

@app.route('/editar', methods=['POST'])
def editar():
    identificador = request.form['identificador']
    grupo = request.form['grupo']
    nombre = request.form['nombre']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    variante = request.form['variante']
    actualmente = request.form['actualmente_la_visita']
    fecha = request.form['fecha']
    observaciones = request.form['observacion']
    ver_en_maps = request.form['ver_en_maps']

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE visitas
            SET nombre=%s, direccion=%s, telefono=%s,
                variante=%s, actualmente_la_visita=%s,
                fecha=%s, observaciones=%s, ver_en_maps=%s
            WHERE identificador=%s;
        """, (nombre, direccion, telefono, variante,
              actualmente, fecha, observaciones, ver_en_maps, identificador))
        conn.commit()
        flash(f"✅ Registro {identificador} editado correctamente")
    except Exception as e:
        conn.rollback()
        flash(f"⚠️ Error al editar el registro: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(f"/?grupo={grupo}&resaltado={identificador}")

if __name__ == '__main__':
    crear_tabla_si_no_existe()
    app.run(debug=True)
