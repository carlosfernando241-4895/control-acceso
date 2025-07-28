
from werkzeug.security import check_password_hash
from datetime import date, datetime
import hashlib
import json
import os
import re

def validar_rut_chileno(rut_completo):

    rut = rut_completo.strip().upper().replace('.', '').replace('-', '')
    # Verificar longitud mínima
    if len(rut) < 2:
        return False
    # Separar cuerpo y dígito verificador
    cuerpo = rut[:-1]
    dv_ingresado = rut[-1]
    # Validar formato básico
    if not cuerpo.isdigit() or not (dv_ingresado.isdigit() or dv_ingresado == 'K'):
        return False
    # Calcular dígito verificador usando secuencia [2,3,4,5,6,7]
    multiplicadores = [2, 3, 4, 5, 6, 7]
    suma = 0
    # Recorrer de derecha a izquierda
    for i, digito in enumerate(reversed(cuerpo)):
        multiplicador = multiplicadores[i % 6]
        suma += int(digito) * multiplicador

    resto = suma % 11
    # Determinar dígito verificador
    if resto == 0:
        dv_calculado = '0'
    elif resto == 1:
        dv_calculado = 'K'
    else:
        dv_calculado = str(11 - resto)

    return dv_ingresado == dv_calculado


class Empleado:
    def __init__(self, nombre, rut, area, empresa="", autorizado_por=""):
        self.nombre = nombre
        self.rut = rut
        self.area = area
        self.empresa = empresa
        self.autorizado_por = autorizado_por
        self.fecha_ingreso = date.today()
        self.activo = True

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"Empleado: {self.nombre} ({self.rut}) - {self.area} - {estado}"

    def validar_rut(self):
        return validar_rut_chileno(self.rut)

    def activar(self):
        self.activo = True
        print(f"Empleado {self.nombre} activado")

    def desactivar(self):
        self.activo = False
        print(f"Empleado {self.nombre} desactivado")

    def puede_acceder(self):
        return self.activo and self.validar_rut()

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'nombre': self.nombre,
            'rut': self.rut,
            'area': self.area,
            'empresa': self.empresa,
            'autorizado_por': self.autorizado_por,
            'fecha_ingreso': self.fecha_ingreso.isoformat(),
            'activo': self.activo
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un empleado desde un diccionario"""
        empleado = cls(
            nombre=data['nombre'],
            rut=data['rut'],
            area=data['area'],
            empresa=data.get('empresa', ''),
            autorizado_por=data.get('autorizado_por', '')
        )
        empleado.fecha_ingreso = datetime.fromisoformat(data['fecha_ingreso']).date()
        empleado.activo = data['activo']
        return empleado

class Usuario:
    def __init__(self, usuario, password_hash, rol, permisos):
        self.usuario = usuario
        self.password_hash = password_hash
        self.rol = rol
        self.permisos = permisos

    def verificar_password(self, password_plain):
        # Usa check_password_hash para comparar correctamente
        return check_password_hash(self.password_hash, password_plain)

    def to_dict(self):
        return {
            "usuario": self.usuario,
            "password_hash": self.password_hash,
            "rol": self.rol,
            "permisos": self.permisos
        }

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()


class Visitante:
    def __init__(self, nombre, rut, empresa, autorizado_por, fecha_entrada=None):
        self.nombre = nombre
        self.rut = rut
        self.empresa = empresa
        self.fecha_entrada = fecha_entrada if fecha_entrada else date.today()
        self.autorizado_por = autorizado_por
        self.activo = True

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"Visitante: {self.nombre} ({self.rut}) - {self.empresa} - Autorizado por: {self.autorizado_por} - {estado}"

    def es_visita_valida(self):
        """Verifica si la visita es para hoy o futura"""
        from datetime import date
        return self.fecha_entrada == date.today()

    def validar_rut(self):
        return validar_rut_chileno(self.rut)

    def puede_acceder(self):
        # Solo puede acceder si esta activo, RUT valido y es el dia de su visita
        return (self.activo and self.validar_rut() and self.fecha_entrada == date.today())

    def verificar_y_expirar(self):
        """Desactiva al visitante si ya no es el día de su visita"""
        from datetime import date
        if self.fecha_entrada != date.today() and self.activo:
            self.activo = False
            print(f"Visitante {self.nombre} expirado automáticamente (fecha: {self.fecha_entrada})")

    def expirar_acceso(self):
        self.activo = False
        print(f"Acceso del visitante {self.nombre} expirado")

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'nombre': self.nombre,
            'rut': self.rut,
            'empresa': self.empresa,
            'fecha_entrada': self.fecha_entrada.isoformat(),
            'autorizado_por': self.autorizado_por,
            'activo': self.activo
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un visitante desde un diccionario"""
        visitante = cls(
            nombre=data['nombre'],
            rut=data['rut'],
            empresa=data['empresa'],
            autorizado_por=data['autorizado_por'],
            fecha_entrada=datetime.fromisoformat(data['fecha_entrada']).date()
        )
        visitante.activo = data['activo']
        return visitante


class Vehiculo:
    def __init__(self, placa, modelo, propietario_tipo, propietario_id):
        self.placa = placa.upper() # Placa siempre en mayusculas
        self.modelo = modelo
        self.propietario_tipo = propietario_tipo # empleado o visitante
        self.propietario_id = propietario_id

    def __str__(self):
        return f"Vehiculo: {self.placa} - {self.modelo} - Propietario: {self.propietario_tipo} ({self.propietario_id})"

    def validar_placa(self):
        """Valida la placa chilena con los formatos vigentes"""
        patrones_validos = [
            r"^[A-Z]{2}\d{3}$",  # AB123
            r"^[A-Z]{3}\d{2}$",  # ABC12
            r"^[A-Z]{2}\d{4}$",  # AB1234
            r"^[A-Z]{4}\d{2}$",  # ABCD12
        ]
        return any(re.fullmatch(patron, self.placa) for patron in patrones_validos)

    def puede_ingresar(self, empleados_list, visitantes_list):
        if not self.validar_placa():
            return False, "Placa inválida"

        # Buscar propietario
        if self.propietario_tipo == 'empleado':
            propietario = next((emp for emp in empleados_list if emp.rut == self.propietario_id), None)
            if not propietario:
                return False, "Empleado no encontrado"
            if not propietario.puede_acceder():
                return False, "Empleado inactivo o sin permiso"
            return True, "Vehículo autorizado (empleado)"

        elif self.propietario_tipo == 'visitante':
            propietario = next((vis for vis in visitantes_list if vis.rut == self.propietario_id), None)
            if not propietario:
                return False, "Visitante no encontrado"
            if not propietario.puede_acceder():
                return False, "Visitante inactivo o visita no válida"
            return True, "Vehículo autorizado (visitante)"

        return False, "Tipo de propietario desconocido"

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'placa': self.placa,
            'modelo': self.modelo,
            'propietario_tipo': self.propietario_tipo,
            'propietario_id': self.propietario_id
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un vehículo desde un diccionario"""
        return cls(
            placa=data['placa'],
            modelo=data['modelo'],
            propietario_tipo=data['propietario_tipo'],
            propietario_id=data['propietario_id']
        )

class LogAcceso:
    """Clase para registrar los accesos y intentos de acceso"""
    def __init__(self, persona_tipo, persona_rut, vehiculo_placa=None,
                 resultado=False, razon="", fecha_hora=None):
        self.persona_tipo = persona_tipo  # 'empleado' o 'visitante'
        self.persona_rut = persona_rut
        self.vehiculo_placa = vehiculo_placa
        self.resultado = resultado  # True: permitido, False: denegado
        self.razon = razon
        self.fecha_hora = fecha_hora if fecha_hora else datetime.now()

    def __str__(self):
        estado = "PERMITIDO" if self.resultado else "DENEGADO"
        tipo_acceso = "VEHÍCULO" if self.vehiculo_placa else "PERSONA"
        fecha_str = self.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")

        if self.vehiculo_placa:
            return f"[{fecha_str}] {tipo_acceso} {self.vehiculo_placa} - {self.persona_tipo} {self.persona_rut} - {estado}"
        else:
            return f"[{fecha_str}] {tipo_acceso} - {self.persona_tipo} {self.persona_rut} - {estado}"

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'persona_tipo': self.persona_tipo,
            'persona_rut': self.persona_rut,
            'vehiculo_placa': self.vehiculo_placa,
            'resultado': self.resultado,
            'razon': self.razon,
            'fecha_hora': self.fecha_hora.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un log desde un diccionario"""
        log = cls(
            persona_tipo=data['persona_tipo'],
            persona_rut=data['persona_rut'],
            vehiculo_placa=data.get('vehiculo_placa'),
            resultado=data['resultado'],
            razon=data['razon'],
            fecha_hora=datetime.fromisoformat(data['fecha_hora'])
        )
        return log


class ControlAcceso:
    """Clase principal que maneja todo el sistema de control de acceso"""

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

        # Crear directorio si no existe
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 Directorio 'data' creado en: {self.data_dir}")

        self.empleados = []
        self.visitantes = []
        self.vehiculos = []
        self.logs = []
        self.cargar_datos()

    def registrar_log(self, persona_tipo, persona_rut="", vehiculo_placa=None, resultado=False, razon=""):
        log = LogAcceso(
            persona_tipo=persona_tipo,
            persona_rut=persona_rut,
            vehiculo_placa=vehiculo_placa,
            resultado=resultado,
            razon=razon,
            fecha_hora=datetime.now()
        )
        self.logs.append(log)
        self.guardar_datos()

    def cargar_datos(self):
        """Carga los datos desde archivos JSON"""
        archivos = {
            'empleados': 'empleados.json',
            'visitantes': 'visitantes.json',
            'vehiculos': 'vehiculos.json',
            'logs': 'logs.json'
        }

        for tipo, archivo in archivos.items():
            try:
                filepath = os.path.join(self.data_dir, archivo)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if tipo == 'empleados':
                        self.empleados = [Empleado.from_dict(emp) for emp in data]
                    elif tipo == 'visitantes':
                        self.visitantes = [Visitante.from_dict(vis) for vis in data]
                    elif tipo == 'vehiculos':
                        self.vehiculos = [Vehiculo.from_dict(veh) for veh in data]
                    elif tipo == 'logs':
                        self.logs = [LogAcceso.from_dict(log) for log in data]
                else:
                    print(f"📁 Archivo {archivo} no existe, se creará automáticamente")

            except json.JSONDecodeError:
                print(f"❌ Error: Archivo {archivo} tiene formato JSON inválido")
            except Exception as e:
                print(f"❌ Error cargando {archivo}: {e}")

    def guardar_datos(self):
        """Guarda todos los datos en archivos JSON
        Versión mejorada con mejor manejo de errores
        """
        try:
            # Crear directorio si no existe
            os.makedirs(self.data_dir, exist_ok=True)

            # Definir archivos y sus datos correspondientes
            archivos_datos = {
                'empleados.json': [emp.to_dict() for emp in self.empleados],
                'visitantes.json': [vis.to_dict() for vis in self.visitantes],
                'vehiculos.json': [veh.to_dict() for veh in self.vehiculos],
                'logs.json': [log.to_dict() for log in self.logs]
            }

            # Guardar cada archivo
            for nombre_archivo, datos in archivos_datos.items():
                filepath = os.path.join(self.data_dir, nombre_archivo)

                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(datos, f, indent=4, ensure_ascii=False)
                    print(f"✅ {nombre_archivo} guardado correctamente")

                except PermissionError:
                    print(f"❌ Error: No se tienen permisos para escribir {nombre_archivo}")
                    return False
                except Exception as e:
                    print(f"❌ Error guardando {nombre_archivo}: {e}")
                    return False

            return True

        except Exception as e:
            print(f"❌ Error general al guardar datos: {e}")
            return False

    def obtener_cantidades(self):
        return {
            'empleados_registrados': len(self.empleados),
            'visitantes_registrados': len(self.visitantes),
            'vehiculos_registrados': len(self.vehiculos)
        }

    def obtener_resumen(self):
        stats = self.obtener_estadisticas_hoy()
        cantidades = {
            'empleados_registrados': len(self.empleados),
            'visitantes_registrados': len(self.visitantes),
            'vehiculos_registrados': len(self.vehiculos)
        }
        resumen = {**cantidades, **stats}
        return resumen

    def agregar_empleado(self, empleado):
        """Agrega un empleado al sistema"""
        # Verificar que no exista el RUT
        if self.buscar_empleado_por_rut(empleado.rut):
            return False, "Ya existe un empleado con ese RUT"

        self.empleados.append(empleado)
        self.guardar_datos()
        return True, "Empleado agregado exitosamente"

    def agregar_visitante(self, visitante):
        """Agrega un visitante al sistema"""
        if self.buscar_visitante_por_rut(visitante.rut):
            return False, "Ya existe un visitante con ese RUT"
        self.visitantes.append(visitante)
        self.guardar_datos()
        return True, "Visitante agregado correctamente"

    def agregar_vehiculo(self, vehiculo):
        """Agrega un vehículo al sistema"""
        # Verificar que no exista la placa
        if self.buscar_vehiculo_por_placa(vehiculo.placa):
            return False, "Ya existe un vehículo con esa patente"

        self.vehiculos.append(vehiculo)
        self.guardar_datos()
        return True, "Vehículo agregado exitosamente"

    def buscar_empleado_por_nombre(self, nombre):
        """Busca empleados por nombre (búsqueda parcial)"""
        nombre_lower = nombre.lower()
        encontrados = []
        for emp in self.empleados:
            if nombre_lower in emp.nombre.lower():
                encontrados.append(emp)
        return encontrados

    def buscar_visitante_por_nombre(self, nombre):
        """Busca visitantes por nombre (búsqueda parcial)"""
        nombre_lower = nombre.lower()
        encontrados = []
        for vis in self.visitantes:
            if nombre_lower in vis.nombre.lower():
                encontrados.append(vis)
        return encontrados

    def buscar_empleado_por_rut(self, rut):
        """Busca un empleado por RUT"""
        for emp in self.empleados:
            if emp.rut == rut:
                return emp
        return None

    def buscar_visitante_por_rut(self, rut):
        """Busca un visitante por RUT"""
        for vis in self.visitantes:
            if vis.rut == rut:
                return vis
        return None

    def actualizar_estado_visitantes(self):
        for v in self.visitantes:
            v.verificar_y_expirar()

    def buscar_vehiculo_por_placa(self, placa):
        """Busca un vehículo por placa"""
        for veh in self.vehiculos:
            if veh.placa == placa.upper():
                return veh
        return None

    def verificar_acceso_persona(self, rut):
        """Verifica si una persona puede acceder"""
        # Buscar primero en empleados
        empleado = self.buscar_empleado_por_rut(rut)
        if empleado:
            resultado = empleado.puede_acceder()
            razon = "Empleado activo" if resultado else "Empleado inactivo o RUT inválido"
            self.registrar_log("empleado", rut, resultado=resultado, razon=razon)
            return resultado, razon

        # Buscar visitante
        visitante = self.buscar_visitante_por_rut(rut)
        if visitante:
            visitante.verificar_y_expirar()
            resultado = visitante.puede_acceder()

            if resultado:
                razon = "Visitante autorizado para hoy"
            else:
                # 👇 Reorganizamos para dar razón más específica
                if visitante.fecha_entrada != date.today():
                    razon = f"Visita expirada: era para {visitante.fecha_entrada}, hoy es {date.today()}"
                elif not visitante.activo:
                    razon = "Visitante inactivo manualmente"
                elif not visitante.validar_rut():
                    razon = "RUT inválido"
                else:
                    razon = "Visitante no autorizado"

            self.registrar_log("visitante", rut, resultado=resultado, razon=razon)
            return resultado, razon

        # Persona no encontrada
        self.registrar_log("desconocido", rut, resultado=False, razon="Persona no registrada")
        return False, "Persona no registrada en el sistema"

    def verificar_acceso_vehiculo(self, placa):
        vehiculo = self.buscar_vehiculo_por_placa(placa)
        if not vehiculo:
            self.registrar_log("vehiculo", placa, resultado=False, razon="Vehículo no registrado")
            return False, "Vehículo no registrado"

        # Buscar propietario según tipo
        if vehiculo.propietario_tipo == 'empleado':
            propietario = self.buscar_empleado_por_rut(vehiculo.propietario_id)
            if not propietario:
                razon = "Empleado propietario no encontrado"
                self.registrar_log("vehiculo", placa, resultado=False, razon=razon)
                return False, razon
            if not propietario.puede_acceder():
                razon = "Empleado inactivo o RUT inválido"
                self.registrar_log("vehiculo", placa, resultado=False, razon=razon)
                return False, razon
            razon = "Vehículo autorizado (empleado)"
            self.registrar_log("vehiculo", placa, resultado=True, razon=razon)
            return True, razon

        elif vehiculo.propietario_tipo == 'visitante':
            propietario = self.buscar_visitante_por_rut(vehiculo.propietario_id)
            if not propietario:
                razon = "Visitante propietario no encontrado"
                self.registrar_log("vehiculo", placa, resultado=False, razon=razon)
                return False, razon

            propietario.verificar_y_expirar()

            if not propietario.puede_acceder():
                if not propietario.activo:
                    razon = f"Visita expirada o visitante inactivo"
                elif propietario.fecha_entrada != date.today():
                    razon = f"Fecha de visita inválida: era para {propietario.fecha_entrada}"
                else:
                    razon = "Visitante sin acceso válido"
                self.registrar_log("vehiculo", placa, resultado=False, razon=razon)
                return False, razon

            razon = "Vehículo autorizado (visitante)"
            self.registrar_log("vehiculo", placa, resultado=True, razon=razon)
            return True, razon

        else:
            razon = "Tipo de propietario inválido"
            self.registrar_log("vehiculo", placa, resultado=False, razon=razon)
            return False, razon

    def obtener_estadisticas_hoy(self):
        """Obtiene estadísticas de acceso del día actual"""
        hoy = date.today()
        logs_hoy = [log for log in self.logs if log.fecha_hora.date() == hoy]

        print(f"Logs hoy: {len(logs_hoy)}")
        for log in logs_hoy:
            print(
                f"{log.persona_tipo} - {log.vehiculo_placa} - Resultado: {log.resultado} - Fecha: {log.fecha_hora} - Tipo: {type(log.resultado)}")

        total_intentos = len(logs_hoy)
        accesos_permitidos = len([log for log in logs_hoy if log.resultado is True])
        accesos_denegados = len([log for log in logs_hoy if log.resultado is False])

        empleados_accesos = len([log for log in logs_hoy if log.persona_tipo == 'empleado' and log.resultado is True])
        visitantes_accesos = len([log for log in logs_hoy if log.persona_tipo == 'visitante' and log.resultado is True])
        vehiculos_accesos = len([log for log in logs_hoy if log.vehiculo_placa and log.resultado is True])

        return {
            'total_intentos': total_intentos,
            'accesos_permitidos': accesos_permitidos,
            'accesos_denegados': accesos_denegados,
            'empleados_accesos': empleados_accesos,
            'visitantes_accesos': visitantes_accesos,
            'vehiculos_accesos': vehiculos_accesos
        }
