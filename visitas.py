from flask import Flask, render_template, request, redirect, flash, session
import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError(
        "❌ DATABASE_URL no está definido. Verifica tus variables de entorno."
    )


def get_connection():
    return psycopg2.connect(DATABASE_URL)


app = Flask(__name__)

app.secret_key = "clave-secreta"


# =========================================================
# CREAR TABLA
# =========================================================

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


# =========================================================
# CARGAR REGISTROS
# =========================================================

def cargar_db(grupo):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            identificador,
            nombre,
            direccion,
            telefono,
            variante,
            entrego,
            actualmente_la_visita,
            observaciones,
            fecha,
            ver_en_maps
        FROM visitas
        WHERE LEFT(identificador, 2) = %s
        ORDER BY identificador ASC;
    """, (grupo,))

    rows = cur.fetchall()

    cur.close()
    conn.close()


    columnas = [
        "identificador",
        "nombre",
        "direccion",
        "telefono",
        "variante",
        "entrego",
        "actualmente_la_visita",
        "observaciones",
        "fecha",
        "ver_en_maps"
    ]


    return [
        dict(zip(columnas, row))
        for row in rows
    ]


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route('/')
def index():

    grupo = request.args.get('grupo', 'QA')

    resaltado = request.args.get('resaltado', '')

    rol = session.get('rol', 'visitante')

    personas = cargar_db(grupo)

    return render_template(
        'index.html',
        personas=personas,
        grupo=grupo,
        rol=rol,
        resaltado=resaltado
    )


# =========================================================
# LOGIN
# =========================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    # =====================================================
    # CONSERVAR EL GRUPO ACTUAL
    # =====================================================

    if request.method == 'POST':

        grupo = request.form.get(
            'grupo',
            'QA'
        ).strip()

    else:

        grupo = request.args.get(
            'grupo',
            'QA'
        ).strip()


    if not grupo:
        grupo = 'QA'


    # =====================================================
    # PROCESAR LOGIN
    # =====================================================

    if request.method == 'POST':

        usuario = request.form['usuario']
        clave = request.form['clave']


        if usuario == "LaEra" and clave == "8824":

            session['rol'] = 'admin'

            flash(
                "✅ Hola Noikni haz ingresado "
                "como administrador"
            )

            # Regresar al mismo grupo desde donde
            # se inició sesión.
            return redirect(
                f"/?grupo={grupo}"
            )


        else:

            flash("Credenciales incorrectas")

            # Si las credenciales son incorrectas,
            # también conservamos el grupo.
            return redirect(
                f"/login?grupo={grupo}"
            )


    return render_template(
        'login.html',
        grupo=grupo
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route('/logout')
def logout():

    # Conservamos el grupo actual al salir.
    grupo = request.args.get(
        'grupo',
        'QA'
    ).strip()


    session.pop('rol', None)

    flash("Has salido del modo administrador")


    return redirect(
        f"/?grupo={grupo}"
    )


# =========================================================
# ACTUALIZAR REGISTRO COMO VISITANTE
# =========================================================

@app.route('/actualizar', methods=['POST'])
def actualizar():

    identificador = request.form.get(
        'identificador',
        ''
    ).strip()

    nueva_obs = request.form.get(
        'observaciones',
        ''
    ).strip()

    nueva_fecha = request.form.get(
        'fecha'
    ) or None

    grupo = request.form.get(
        'grupo',
        ''
    ).strip()


    # La fecha es obligatoria para actualizar una visita

    if not nueva_fecha:

        flash(
            f"⚠️ Por favor, agrega una fecha antes de actualizar "
            f"el registro {identificador}"
        )

        return redirect(
            f"/?grupo={grupo}&resaltado={identificador}"
        )


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            UPDATE visitas
            SET
                observaciones =
                    COALESCE(observaciones, '') ||
                    CASE
                        WHEN %s <> ''
                        THEN E'\n- ' || %s
                        ELSE ''
                    END,

                fecha = %s

            WHERE identificador = %s;
        """, (
            nueva_obs,
            nueva_obs,
            nueva_fecha,
            identificador
        ))


        filas_afectadas = cur.rowcount

        conn.commit()


        if filas_afectadas > 0:

            flash(
                f"✅ cualtitok noikni, Registro {identificador} "
                f"actualizado correctamente"
            )

        else:

            flash(
                f"⚠️ No se encontró el registro "
                f"{identificador}"
            )


    except Exception as e:

        conn.rollback()

        flash(
            f"⚠️ Error al actualizar el registro: {e}"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        f"/?grupo={grupo}&resaltado={identificador}"
    )


# =========================================================
# AGREGAR NUEVO REGISTRO
# =========================================================

@app.route('/nuevo', methods=['POST'])
def nuevo():

    identificador = request.form.get(
        'identificador',
        ''
    ).strip()

    nombre = request.form.get(
        'nombre',
        ''
    ).strip()

    direccion = request.form.get(
        'direccion',
        ''
    ).strip()

    telefono = request.form.get(
        'telefono',
        ''
    ).strip()

    variante = request.form.get(
        'variante',
        ''
    ).strip()

    actualmente = request.form.get(
        'actualmente_la_visita',
        ''
    ).strip()

    observaciones = request.form.get(
        'observaciones',
        ''
    ).strip()

    fecha = request.form.get(
        'fecha'
    ) or None

    ver_en_maps = request.form.get(
        'ver_en_maps',
        ''
    ).strip()

    grupo = request.form.get(
        'grupo',
        ''
    ).strip()


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            INSERT INTO visitas (
                identificador,
                nombre,
                direccion,
                telefono,
                variante,
                actualmente_la_visita,
                observaciones,
                fecha,
                ver_en_maps
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
        """, (
            identificador,
            nombre,
            direccion,
            telefono,
            variante,
            actualmente,
            observaciones,
            fecha,
            ver_en_maps
        ))


        conn.commit()


        flash(
            f"✅ Nuevo registro {identificador} "
            f"agregado correctamente"
        )


    except Exception as e:

        conn.rollback()

        flash(
            f"⚠️ Error al agregar el registro: {e}"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        f"/?grupo={grupo}&resaltado={identificador}"
    )


# =========================================================
# EDITAR REGISTRO COMO ADMINISTRADOR
# =========================================================

@app.route('/editar', methods=['POST'])
def editar():

    identificador_original = request.form.get(
        'identificador_original',
        ''
    ).strip()

    nuevo_identificador = request.form.get(
        'identificador',
        ''
    ).strip()

    grupo = request.form.get(
        'grupo',
        ''
    ).strip()

    nombre = request.form.get(
        'nombre',
        ''
    ).strip()

    direccion = request.form.get(
        'direccion',
        ''
    ).strip()

    telefono = request.form.get(
        'telefono',
        ''
    ).strip()

    variante = request.form.get(
        'variante',
        ''
    ).strip()

    actualmente = request.form.get(
        'actualmente_la_visita',
        ''
    ).strip()

    fecha = request.form.get(
        'fecha'
    ) or None

    observaciones = request.form.get(
        'observaciones',
        ''
    ).strip()

    ver_en_maps = request.form.get(
        'ver_en_maps',
        ''
    ).strip()


    # =====================================================
    # VALIDAR IDENTIFICADOR ORIGINAL
    # =====================================================

    if not identificador_original:

        flash(
            "⚠️ No se recibió el identificador original "
            "del registro."
        )

        return redirect(
            f"/?grupo={grupo}"
        )


    # =====================================================
    # VALIDAR NUEVO IDENTIFICADOR
    # =====================================================

    if not nuevo_identificador:

        flash(
            "⚠️ El identificador no puede estar vacío."
        )

        return redirect(
            f"/?grupo={grupo}"
            f"&resaltado={identificador_original}"
        )


    if len(nuevo_identificador) > 10:

        flash(
            "⚠️ El identificador no puede tener más de "
            "10 caracteres."
        )

        return redirect(
            f"/?grupo={grupo}"
            f"&resaltado={identificador_original}"
        )


    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # COMPROBAR SI EL NUEVO IDENTIFICADOR YA EXISTE
        # =================================================

        cur.execute("""
            SELECT 1
            FROM visitas
            WHERE identificador = %s
              AND identificador <> %s;
        """, (
            nuevo_identificador,
            identificador_original
        ))


        registro_existente = cur.fetchone()


        if registro_existente:

            flash(
                f"⚠️ El identificador "
                f"{nuevo_identificador} ya existe. "
                f"No se puede utilizar."
            )

            conn.rollback()

            return redirect(
                f"/?grupo={grupo}"
                f"&resaltado={identificador_original}"
            )


        # =================================================
        # ACTUALIZAR REGISTRO
        # =================================================

        cur.execute("""
            UPDATE visitas

            SET
                identificador = %s,
                nombre = %s,
                direccion = %s,
                telefono = %s,
                variante = %s,
                actualmente_la_visita = %s,
                fecha = %s,
                observaciones = %s,
                ver_en_maps = %s

            WHERE identificador = %s;
        """, (
            nuevo_identificador,
            nombre,
            direccion,
            telefono,
            variante,
            actualmente,
            fecha,
            observaciones,
            ver_en_maps,
            identificador_original
        ))


        filas_afectadas = cur.rowcount

        conn.commit()


        # =================================================
        # RESULTADO
        # =================================================

        if filas_afectadas > 0:

            if identificador_original != nuevo_identificador:

                flash(
                    f"✅ Registro {identificador_original} "
                    f"cambiado a {nuevo_identificador} "
                    f"y editado correctamente."
                )

            else:

                flash(
                    f"✅ cualtitok noikni, Registro "
                    f"{nuevo_identificador} "
                    f"editado correctamente."
                )

        else:

            flash(
                f"⚠️ No se encontró el registro "
                f"{identificador_original}"
            )


    except Exception as e:

        conn.rollback()

        flash(
            f"⚠️ Error al editar el registro: {e}"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        f"/?grupo={grupo}"
        f"&resaltado={nuevo_identificador}"
    )


# =========================================================
# ELIMINAR REGISTRO COMO ADMINISTRADOR
# =========================================================

@app.route('/eliminar', methods=['POST'])
def eliminar():

    # Verificar que realmente sea administrador
    if session.get('rol') != 'admin':

        flash(
            "⚠️ No tienes permisos para eliminar registros"
        )

        grupo = request.form.get(
            'grupo',
            'QA'
        ).strip()

        return redirect(
            f"/?grupo={grupo}"
        )


    identificador = request.form.get(
        'identificador',
        ''
    ).strip()

    grupo = request.form.get(
        'grupo',
        ''
    ).strip()


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            DELETE FROM visitas
            WHERE identificador = %s;
        """, (
            identificador,
        ))


        filas_afectadas = cur.rowcount

        conn.commit()


        if filas_afectadas > 0:

            flash(
                f"✅ Registro {identificador} "
                f"eliminado correctamente"
            )

        else:

            flash(
                f"⚠️ No se encontró el registro "
                f"{identificador}"
            )


    except Exception as e:

        conn.rollback()

        flash(
            f"⚠️ Error al eliminar el registro: {e}"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        f"/?grupo={grupo}"
    )


# =========================================================
# INICIAR APLICACIÓN
# =========================================================

if __name__ == '__main__':

    crear_tabla_si_no_existe()

    app.run(debug=True)
