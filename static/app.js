const apiBase = 'http://127.0.0.1:5000';

// Limpia y formatea RUT
function cleanRUT(rut) {
    return rut.replace(/\./g, '').replace(/-/g, '').toUpperCase();
}
// Cargar Usuarios
function verificarPermiso(permiso) {
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  return usuario && usuario.permisos.includes(permiso);
}

function cerrarSesion() {
  localStorage.removeItem("usuario");
  window.location.href = "/sesion";
}

// ==================== BÚSQUEDAS EN TABLAS ====================
function searchEmployees() {
    const query = document.getElementById('employee-search').value.toLowerCase();
    document.querySelectorAll('#employees-tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function searchVisitors() {
    const query = document.getElementById('visitor-search').value.toLowerCase();
    document.querySelectorAll('#visitors-tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function searchVehicles() {
    const query = document.getElementById('vehicle-search').value.toLowerCase();
    document.querySelectorAll('#vehicles-tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

// ==================== TOGGLE INPUT CONTROL DE ACCESO ====================
function toggleAccessInput() {
    const tipo = document.getElementById('access-type').value;
    const label = document.getElementById('access-input-label');
    const input = document.getElementById('access-input');

    if (tipo === 'person') {
        label.textContent = 'RUT de la Persona';
        input.placeholder = 'Ej: 12345678-9';
    } else {
        label.textContent = 'Placa del Vehículo';
        input.placeholder = 'Ej: ABC123 o ABCD12';
    }
}

// ==================== EMPLEADOS ====================
function formatDate(fechaISO) {
    if (!fechaISO) return '';
    const [anio, mes, dia] = fechaISO.split('-');
    return `${dia}/${mes}/${anio}`;
}
async function loadEmployees() {
    try {
        const res = await fetch(`${apiBase}/empleados`);
        if (!res.ok) throw new Error('Error cargando empleados');
        const data = await res.json();

        const tbody = document.getElementById('employees-tbody');
        tbody.innerHTML = '';

        data.forEach(emp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="status-${emp.activo ? 'active' : 'inactive'}">${emp.activo ? '✅ Activo' : '❌ Inactivo'}</span></td>
                <td>${emp.rut}</td>
                <td>${emp.nombre}</td>
                <td>${emp.area}</td>
                <td>${emp.empresa}</td>
                <td>${formatDate(emp.fecha_ingreso)}</td>
                <td>
                    <button class="btn btn-warning" onclick="toggleEmployeeStatus('${emp.rut}')">${emp.activo ? 'Desactivar' : 'Activar'}</button>
                    <button class="btn btn-danger" onclick="deleteEmployee('${emp.rut}')">Eliminar</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        alert(error.message);
    }
}

async function addEmployee() {
    const nombre = document.getElementById('emp-name').value.trim();
    const rut = cleanRUT(document.getElementById('emp-rut').value.trim());
    const area = document.getElementById('emp-area').value.trim();
    const empresa = document.getElementById('emp-company').value.trim();
    const autorizado_por = document.getElementById('emp-authorized').value.trim();

    if (!nombre || !rut || !area) {
        alert('Nombre, RUT y Área son obligatorios.');
        return;
    }

    try {
        const res = await fetch(`${apiBase}/empleados`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, rut, area, empresa, autorizado_por })
        });
        const result = await res.json();

        alert(result.msg || 'Empleado agregado.');
        clearEmployeeForm();
        loadEmployees();
    } catch (error) {
        alert('Error al agregar empleado.');
    }
}

function clearEmployeeForm() {
    document.getElementById('emp-name').value = '';
    document.getElementById('emp-rut').value = '';
    document.getElementById('emp-area').value = '';
    document.getElementById('emp-company').value = '';
    document.getElementById('emp-authorized').value = '';
}

async function toggleEmployeeStatus(rut) {
    try {
        const res = await fetch(`${apiBase}/empleados/${rut}`, { method: 'PUT' });
        const result = await res.json();

        alert(result.msg || 'Estado actualizado');
        loadEmployees();
    } catch {
        alert('Error al actualizar estado.');
    }
}

async function deleteEmployee(rut) {
    if (!confirm('¿Seguro que deseas eliminar este empleado?')) return;

    try {
        const res = await fetch(`${apiBase}/empleados/${rut}`, { method: 'DELETE' });
        const result = await res.json();

        alert(result.msg || 'Empleado eliminado.');
        loadEmployees();
    } catch {
        alert('Error al eliminar empleado.');
    }
}

// ==================== VISITANTES ====================
async function loadVisitors() {
    try {
        const res = await fetch(`${apiBase}/visitantes`);
        if (!res.ok) throw new Error('Error cargando visitantes');
        const data = await res.json();

        const tbody = document.getElementById('visitors-tbody');
        tbody.innerHTML = '';

        data.forEach(vis => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="status-${vis.activo ? 'active' : 'inactive'}">${vis.activo ? '✅ Activo' : '❌ Inactivo'}</span></td>
                <td>${vis.rut}</td>
                <td>${vis.nombre}</td>
                <td>${vis.empresa}</td>
                <td>${formatFecha(vis.fecha_entrada)}</td>
                <td>${vis.autorizado_por}</td>
                <td>
                    <button class="btn btn-warning" onclick="toggleVisitorStatus('${vis.rut}')">${vis.activo ? 'Desactivar' : 'Activar'}</button>
                    <button class="btn btn-danger" onclick="deleteVisitor('${vis.rut}')">Eliminar</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        alert(error.message);
    }
}

async function addVisitor() {
    const nombre = document.getElementById('vis-name').value.trim();
    const rut = cleanRUT(document.getElementById('vis-rut').value.trim());
    const empresa = document.getElementById('vis-company').value.trim();
    const autorizado_por = document.getElementById('vis-authorized').value.trim();
    const fecha_visita = document.getElementById('vis-date').value;

    if (!nombre || !rut) {
        alert('Nombre y RUT son obligatorios.');
        return;
    }

    // ✅ Convertir fecha a dd/mm/yyyy
    let fecha_entrada = '';
    if (fecha_visita) {
        const partes = fecha_visita.split('-'); // ["2025", "07", "21"]
        fecha_entrada = `${partes[2]}/${partes[1]}/${partes[0]}`; // "21/07/2025"
    }

    try {
        const res = await fetch(`${apiBase}/visitantes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, rut, empresa, autorizado_por, fecha_entrada })
        });
        const result = await res.json();

        alert(result.msg || 'Visitante agregado.');
        clearVisitorForm();
        loadVisitors();
    } catch {
        alert('Error al agregar visitante.');
    }
}
function formatFecha(fechaISO) {
    if (!fechaISO) return '';
    const [yyyy, mm, dd] = fechaISO.split('-');
    return `${dd}/${mm}/${yyyy}`;
}

function clearVisitorForm() {
    document.getElementById('vis-name').value = '';
    document.getElementById('vis-rut').value = '';
    document.getElementById('vis-company').value = '';
    document.getElementById('vis-authorized').value = '';
    document.getElementById('vis-date').value = '';
}

async function toggleVisitorStatus(rut) {
    try {
        const res = await fetch(`${apiBase}/visitantes/${rut}`, { method: 'PUT' });
        const result = await res.json();

        alert(result.msg || 'Estado actualizado');
        loadVisitors();
    } catch {
        alert('Error al actualizar estado.');
    }
}

async function deleteVisitor(rut) {
    if (!confirm('¿Seguro que deseas eliminar este visitante?')) return;

    try {
        const res = await fetch(`${apiBase}/visitantes/${rut}`, { method: 'DELETE' });
        const result = await res.json();

        alert(result.msg || 'Visitante eliminado.');
        loadVisitors();
    } catch {
        alert('Error al eliminar visitante.');
    }
}

// ==================== VEHÍCULOS ====================
async function loadVehicles() {
    try {
        const res = await fetch(`${apiBase}/vehiculos`);
        if (!res.ok) throw new Error('Error cargando vehículos');
        const data = await res.json();

        const tbody = document.getElementById('vehicles-tbody');
        tbody.innerHTML = '';

        data.forEach(veh => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${veh.placa}</td>
                <td>${veh.modelo}</td>
                <td>${veh.propietario_tipo}</td>
                <td>${veh.propietario_id}</td>
                <td>
                    <button class="btn btn-danger" onclick="deleteVehicle('${veh.placa}')">Eliminar</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        alert(error.message);
    }
}

async function addVehicle() {
    const placa = document.getElementById('veh-plate').value.trim();
    const modelo = document.getElementById('veh-model').value.trim();
    const propietario_tipo = document.getElementById('veh-owner-type').value;
    const propietario_id = cleanRUT(document.getElementById('veh-owner-rut').value.trim());

    if (!placa || !modelo || !propietario_tipo || !propietario_id) {
        alert('Todos los campos son obligatorios.');
        return;
    }

    try {
        const res = await fetch(`${apiBase}/vehiculos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa, modelo, propietario_tipo, propietario_id })
        });
        const result = await res.json();

        alert(result.msg || 'Vehículo agregado.');
        clearVehicleForm();
        loadVehicles();
    } catch {
        alert('Error al agregar vehículo.');
    }
}

function clearVehicleForm() {
    document.getElementById('veh-plate').value = '';
    document.getElementById('veh-model').value = '';
    document.getElementById('veh-owner-type').value = '';
    document.getElementById('veh-owner-rut').value = '';
}

async function deleteVehicle(placa) {
    if (!confirm('¿Seguro que deseas eliminar este vehículo?')) return;

    try {
        const res = await fetch(`${apiBase}/vehiculos/${placa}`, { method: 'DELETE' });
        const result = await res.json();

        alert(result.msg || 'Vehículo eliminado.');
        loadVehicles();
    } catch {
        alert('Error al eliminar vehículo.');
    }
}

// ==================== CONTROL DE ACCESO ====================
async function verifyAccess() {
    const tipo = document.getElementById('access-type').value; // 'persona' o 'vehiculo'
    const valor = document.getElementById('access-input').value.trim();

    if (!valor) {
        alert('Debe ingresar un valor para verificar acceso.');
        return;
    }

    let url = '';
    let payload = {};

    if (tipo === 'persona') {
        url = `${apiBase}/acceso/persona`;
        payload = { rut: valor };
    } else if (tipo === 'vehiculo') {
        url = `${apiBase}/acceso/vehiculo`;
        payload = { placa: valor };
    } else {
        alert('Tipo de acceso inválido.');
        return;
    }

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await res.json();

        const resultDiv = document.getElementById('access-result');
        resultDiv.textContent = result.mensaje;  // ✅ usa el campo correcto del backend
        resultDiv.className = 'access-result ' + (result.success ? 'access-granted' : 'access-denied');

        loadLogs();  // si quieres recargar los logs recientes

    } catch (err) {
        console.error(err);
        alert('Error verificando acceso.');
    }
}
function toggleAccessInput() {
    const tipo = document.getElementById('access-type').value;
    const input = document.getElementById('access-input');
    const label = document.getElementById('access-input-label');

    if (tipo === 'persona') {
        label.textContent = 'RUT de la Persona';
        input.placeholder = 'Ej: 12345678-9';
        input.value = ''; // Opcional: limpiar campo
    } else if (tipo === 'vehiculo') {
        label.textContent = 'Placa del Vehículo';
        input.placeholder = 'Ej: ABCD12 o ABC12';
        input.value = ''; // Opcional: limpiar campo
    }
}

// ==================== LOGS ====================
async function loadLogs() {
    try {
        const res = await fetch(`${apiBase}/logs`);
        if (!res.ok) throw new Error('Error cargando logs');
        const data = await res.json();

        const logsContainer = document.getElementById('access-logs');
        logsContainer.innerHTML = '';

        data.reverse().forEach(log => {
            const div = document.createElement('div');

            const fecha = new Date(log.fecha_hora).toLocaleString();
            const tipo = log.vehiculo_placa ? 'Vehículo' : 'Persona';
            const valor = log.vehiculo_placa || log.persona_rut;
            const estado = log.resultado ? '✅ Permitido' : '❌ Denegado';
            const razon = log.razon || 'Sin razón especificada';

            div.className = `log-entry ${log.resultado ? 'log-granted' : 'log-denied'}`;
            div.textContent = `[${fecha}] ${tipo}: ${valor} => ${estado} (${razon})`;
            logsContainer.appendChild(div);
        });
    } catch (error) {
        alert(error.message);
    }
}
// ==================== ESTADÍSTICAS ====================
async function updateStats() {
    try {
        const res = await fetch(`${apiBase}/reportes/resumen`); // Cambié aquí la ruta
        if (!res.ok) throw new Error('Error cargando estadísticas');
        const stats = await res.json();

        document.getElementById('total-employees').textContent = stats.empleados_registrados;
        document.getElementById('total-visitors').textContent = stats.visitantes_registrados;
        document.getElementById('total-vehicles').textContent = stats.vehiculos_registrados;
        document.getElementById('total-logs').textContent = stats.total_intentos;
        document.getElementById('today-access').textContent = stats.accesos_permitidos;
        document.getElementById('today-denegados').textContent = stats.accesos_denegados;
    } catch (error) {
        alert(error.message);
    }
}

// ==================== EXPORTAR DATOS  ====================
async function exportarDatos() {
    try {
        const res = await fetch(`${apiBase}/exportar/datos`);
        if (!res.ok) throw new Error("Error exportando datos");

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'datos_control_acceso.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert(error.message);
    }
}
function showSection(sectionId) {
  // Quita la clase active de todos los botones de navegación
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Pon la clase active al botón que corresponde al sectionId
  const btnToActivate = Array.from(document.querySelectorAll('.nav-btn')).find(btn => {
    return btn.getAttribute('onclick').includes(`showSection('${sectionId}')`);
  });
  if (btnToActivate) btnToActivate.classList.add('active');

  // Oculta todas las secciones
  document.querySelectorAll('.section').forEach(sec => {
    sec.classList.remove('active');
    sec.style.display = 'none';
  });

  // Muestra solo la sección solicitada
  const section = document.getElementById(sectionId);
  if (section) {
    section.classList.add('active');
    section.style.display = 'block';
  }
}

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    loadEmployees();
    loadVisitors();
    loadVehicles();
    loadLogs();
    updateStats();
    toggleAccessInput(); // para poner label e input correctos inicialmente
});