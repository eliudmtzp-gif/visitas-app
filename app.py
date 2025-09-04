from flask import Flask, render_template, request, redirect
import pandas as pd

app = Flask(__name__)

# Cargar datos desde Excel y crear copia interna
def cargar_datos():
    df = pd.read_excel('datos.xlsx')
    df.to_csv('db.csv', index=False)
    return df

# Leer la copia interna
def cargar_db():
    return pd.read_csv('db.csv')

@app.route('/')
def index():
    grupo = request.args.get('grupo', 'General')  # Puedes cambiar 'General' por el nombre de un grupo real
    df = cargar_db()

    # Aquí puedes filtrar por grupo si decides usar una columna como 'VARIANTE' o 'ENTREGÓ'
    personas = df[df['VARIANTE'] == grupo] if 'VARIANTE' in df.columns else df

    return render_template('index.html', personas=personas.to_dict(orient='records'), grupo=grupo)

@app.route('/actualizar', methods=['POST'])
def actualizar():
    id_persona = int(request.form['id'])
    nueva_obs = request.form['observacion']
    nueva_fecha = request.form['fecha']
    df = cargar_db()
    df.loc[df['Id'] == id_persona, 'OBSERVACIONES'] = nueva_obs
    df.loc[df['Id'] == id_persona, 'FECHA'] = nueva_fecha
    df.to_csv('db.csv', index=False)
    return redirect(f"/?grupo={request.form['grupo']}")

if __name__ == '__main__':
    cargar_datos()
    app.run(debug=True)