from flask import Flask, request, jsonify, render_template, send_file, session, redirect
from src.logica import ControlAcceso, Empleado, Visitante, Vehiculo, validar_rut_chileno, Usuario
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, json
import io
import pandas as pd
app = Flask(__name__)
CORS(app)
app.secret_key = 'cafemoga2201'
sistema = ControlAcceso()

# --- PÁGINA PRINCIPAL ---
@app.route('/')
def home():
    return render_template('sesion.html')
@app.route('/sesion')
def sesion():
    session.clear()  # Limpia la sesión si es necesario
    return render_template('sesion.html')
@app.route('/index.html')
def index():
    if 'usuario' in session:
        return render_template('index.html')
    else:
        return redirect('/sesion')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'data', 'usuarios.json')

def cargar_usuarios():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Usuario(u["usuario"], u["password"], u["rol"], u["permisos"]) for u in data]

def guardar_usuarios(usuarios):
    with open(USERS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=2)
# Endpoint para login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('usuario')
    password = data.get('password')

    usuarios = cargar_usuarios()

    for u in usuarios:
        if u.usuario == username and u.verificar_password(password):
            session['usuario'] = u.usuario  # <--- Aquí guardamos al usuario
            return jsonify({
                "success": True,
                "usuario": u.usuario,
                "rol": u.rol,
                "permisos": u.permisos
            })

    return jsonify({"success": False, "message": "Usuario o contraseña incorrecta"}), 401


# Crear usuario ejemplo para probar (opcional)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    usuarios = cargar_usuarios()

    if any(u['usuario'] == data['usuario'] for u in usuarios):
        return jsonify({"success": False, "mensaje": "Usuario ya existe"}), 400

    hashed_pw = generate_password_hash(data['password'])

    nuevo_usuario = {
        "usuario": data['usuario'],
        "password": hashed_pw,
        "rol": data.get('rol', 'usuario'),
        "permisos": data.get('permisos', [])
    }
    usuarios.append(nuevo_usuario)
    guardar_usuarios(usuarios)
    return jsonify({"success": True, "mensaje": "Usuario registrado correctamente"})

# --- RUTAS EMPLEADOS ---
@app.route('/empleados', methods=['GET'])
def listar_empleados():
    empleados = [emp.to_dict() for emp in sistema.empleados]
    return jsonify(empleados)

@app.route('/empleados', methods=['POST'])
def agregar_empleado():
    data = request.json
    rut = data.get('rut', '').upper()
    if not validar_rut_chileno(rut):
        return jsonify({"success": False, "msg": "RUT inválido"}), 400

    # ❗ Verificar que no exista como visitante
    if sistema.buscar_visitante_por_rut(rut):
        return jsonify({"success": False, "msg": "El RUT ya pertenece a un visitante registrado"}), 400

    empleado = Empleado(
        nombre=data.get('nombre', ''),
        rut=rut,
        area=data.get('area', ''),
        empresa=data.get('empresa', ''),
        autorizado_por=data.get('autorizado_por', '')
    )
    resultado, mensaje = sistema.agregar_empleado(empleado)
    if resultado:
        sistema.guardar_datos()
        return jsonify({"success": True, "msg": mensaje})
    return jsonify({"success": False, "msg": mensaje}), 400

@app.route('/empleados/<rut>', methods=['GET'])
def obtener_empleado(rut):
    empleado = sistema.buscar_empleado_por_rut(rut.upper())
    if empleado:
        return jsonify(empleado.to_dict())
    return jsonify({"msg": "Empleado no encontrado"}), 404

@app.route('/empleados/<rut>', methods=['DELETE'])
def eliminar_empleado(rut):
    empleado = sistema.buscar_empleado_por_rut(rut.upper())
    if not empleado:
        return jsonify({"msg": "Empleado no encontrado"}), 404
    sistema.empleados.remove(empleado)
    sistema.guardar_datos()
    return jsonify({"msg": "Empleado eliminado"})

@app.route('/empleados/<rut>', methods=['PUT'])
def toggle_estado_empleado(rut):
    empleado = sistema.buscar_empleado_por_rut(rut.upper())
    if not empleado:
        return jsonify({"msg": "Empleado no encontrado"}), 404
    empleado.activo = not empleado.activo
    sistema.guardar_datos()
    estado = "activado" if empleado.activo else "desactivado"
    return jsonify({"msg": f"Empleado {estado} correctamente"})

# --- RUTAS VISITANTES ---
@app.route('/visitantes', methods=['GET'])
def listar_visitantes():
    visitantes = [v.to_dict() for v in sistema.visitantes]
    return jsonify(visitantes)

from datetime import datetime

@app.route('/visitantes', methods=['POST'])
def agregar_visitante():
    data = request.json
    rut = data.get('rut', '').upper()
    if not validar_rut_chileno(rut):
        return jsonify({"success": False, "msg": "RUT inválido"}), 400

    # ❗ Verificar que no exista como empleado
    if sistema.buscar_empleado_por_rut(rut):
        return jsonify({"success": False, "msg": "El RUT ya pertenece a un empleado registrado"}), 400

    fecha_entrada_str = data.get('fecha_entrada')
    try:
        fecha_entrada = datetime.strptime(fecha_entrada_str, '%d/%m/%Y').date()
    except ValueError:
        return jsonify({"success": False, "msg": "Formato de fecha inválido. Usa DD/MM/AAAA"}), 400

    visitante = Visitante(
        nombre=data.get('nombre', ''),
        rut=rut,
        empresa=data.get('empresa', ''),
        autorizado_por=data.get('autorizado_por', ''),
        fecha_entrada=fecha_entrada
    )
    resultado, mensaje = sistema.agregar_visitante(visitante)
    if resultado:
        sistema.guardar_datos()
        return jsonify({"success": True, "msg": mensaje})
    return jsonify({"success": False, "msg": mensaje}), 400

@app.route('/visitantes/<rut>', methods=['GET'])
def obtener_visitante(rut):
    rut = rut.upper()
    sistema.actualizar_estado_visitantes()   # ⬅️ Primero actualizas todo
    sistema.guardar_datos()                  # ⬅️ Luego guardas
    visitante = sistema.buscar_visitante_por_rut(rut)  # ⬅️ Y ahora lo buscas actualizado
    if visitante:
        return jsonify(visitante.to_dict())
    return jsonify({"msg": "Visitante no encontrado"}), 404

@app.route('/visitantes/<rut>', methods=['DELETE'])
def eliminar_visitante(rut):
    visitante = sistema.buscar_visitante_por_rut(rut.upper())
    if not visitante:
        return jsonify({"msg": "Visitante no encontrado"}), 404
    sistema.visitantes.remove(visitante)
    sistema.guardar_datos()
    return jsonify({"msg": "Visitante eliminado"})

@app.route('/visitantes/<rut>', methods=['PUT'])
def toggle_estado_visitante(rut):
    visitante = sistema.buscar_visitante_por_rut(rut.upper())
    if not visitante:
        return jsonify({"msg": "Visitante no encontrado"}), 404
    visitante.activo = not visitante.activo
    sistema.guardar_datos()
    estado = "activado" if visitante.activo else "desactivado"
    return jsonify({"msg": f"Visitante {estado} correctamente"})

# --- RUTAS VEHÍCULOS ---
@app.route('/vehiculos', methods=['GET'])
def listar_vehiculos():
    vehiculos = [v.to_dict() for v in sistema.vehiculos]
    return jsonify(vehiculos)

@app.route('/vehiculos', methods=['POST'])
def agregar_vehiculo():
    data = request.json
    placa = data.get('placa', '').upper()
    modelo = data.get('modelo', '')
    propietario_tipo = data.get('propietario_tipo', '').lower()
    propietario_id = data.get('propietario_id', '').upper()

    if not all([placa, modelo, propietario_tipo, propietario_id]):
        return jsonify({"success": False, "msg": "Todos los campos son obligatorios"}), 400

    if propietario_tipo not in ['empleado', 'visitante']:
        return jsonify({"success": False, "msg": "Tipo de propietario debe ser 'empleado' o 'visitante'"}), 400

    # ❗ Validar que el propietario exista
    if propietario_tipo == 'empleado':
        if not sistema.buscar_empleado_por_rut(propietario_id):
            return jsonify({"success": False, "msg": "Empleado no encontrado"}), 404
    elif propietario_tipo == 'visitante':
        if not sistema.buscar_visitante_por_rut(propietario_id):
            return jsonify({"success": False, "msg": "Visitante no encontrado"}), 404

    # ❗ Validar si ya existe la placa
    if sistema.buscar_vehiculo_por_placa(placa):
        return jsonify({"success": False, "msg": "Ya existe un vehículo con esa placa"}), 400

    vehiculo = Vehiculo(placa, modelo, propietario_tipo, propietario_id)
    if not vehiculo.validar_placa():
        return jsonify({"success": False, "msg": "Patente inválida"}), 400

    resultado, mensaje = sistema.agregar_vehiculo(vehiculo)
    if resultado:
        sistema.guardar_datos()
        return jsonify({"success": True, "msg": mensaje})
    return jsonify({"success": False, "msg": mensaje}), 400

@app.route('/vehiculos/<placa>', methods=['GET'])
def obtener_vehiculo(placa):
    vehiculo = sistema.buscar_vehiculo_por_placa(placa.upper())
    if vehiculo:
        return jsonify(vehiculo.to_dict())
    return jsonify({"msg": "Vehículo no encontrado"}), 404

@app.route('/vehiculos/<placa>', methods=['DELETE'])
def eliminar_vehiculo(placa):
    vehiculo = sistema.buscar_vehiculo_por_placa(placa.upper())
    if not vehiculo:
        return jsonify({"msg": "Vehículo no encontrado"}), 404
    sistema.vehiculos.remove(vehiculo)
    sistema.guardar_datos()
    return jsonify({"msg": "Vehículo eliminado"})

# --- RUTAS CONTROL DE ACCESO ---
@app.route('/acceso/persona', methods=['POST'])
def verificar_acceso_persona():
    rut = request.json.get('rut', '').replace('.', '').replace('-', '').upper()
    if not validar_rut_chileno(rut):
        return jsonify({"success": False, "mensaje": "RUT inválido"}), 400
    resultado, mensaje = sistema.verificar_acceso_persona(rut)
    return jsonify({"success": resultado, "mensaje": mensaje})

@app.route('/acceso/vehiculo', methods=['POST'])
def verificar_acceso_vehiculo():
    placa = request.json.get('placa', '').upper()
    resultado, mensaje = sistema.verificar_acceso_vehiculo(placa)
    return jsonify({"success": resultado, "mensaje": mensaje})


# --- RUTAS REPORTES Y LOGS ---
@app.route('/reportes/estadisticas', methods=['GET'])
def estadisticas():
    return jsonify(sistema.obtener_estadisticas_hoy())

@app.route('/logs', methods=['GET'])
def obtener_logs():
    logs = [log.to_dict() for log in sistema.logs]
    return jsonify(logs)
@app.route('/reportes/resumen', methods=['GET'])
def resumen():
    return jsonify(sistema.obtener_resumen())
@app.route('/exportar/datos', methods=['GET'])
def exportar_datos():
    # Convertir listas a DataFrames
    df_empleados = pd.DataFrame([emp.to_dict() for emp in sistema.empleados])
    df_visitantes = pd.DataFrame([vis.to_dict() for vis in sistema.visitantes])
    df_vehiculos = pd.DataFrame([veh.to_dict() for veh in sistema.vehiculos])
    df_logs = pd.DataFrame([log.to_dict() for log in sistema.logs])

    # Crear un Excel en memoria con varias hojas
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_empleados.to_excel(writer, index=False, sheet_name='Empleados')
        df_visitantes.to_excel(writer, index=False, sheet_name='Visitantes')
        df_vehiculos.to_excel(writer, index=False, sheet_name='Vehiculos')
        df_logs.to_excel(writer, index=False, sheet_name='Logs')

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name='datos_control_acceso.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    resumen = sistema.obtener_resumen()
    print(f"Empleados registrados: {resumen['empleados_registrados']}")
    print(f"Visitantes registrados: {resumen['visitantes_registrados']}")
    print(f"Vehículos registrados: {resumen['vehiculos_registrados']}")
    print(f"Intentos de acceso hoy: {resumen['total_intentos']}")
    print(f"Accesos permitidos hoy: {resumen['accesos_permitidos']}")
    print(f"Accesos denegados hoy: {resumen['accesos_denegados']}")
