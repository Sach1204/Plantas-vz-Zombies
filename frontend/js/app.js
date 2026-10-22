const API_URL = 'http://127.0.0.1:5000/api/v1';
const POLL_INTERVAL_MS = 5000;

const authPanel = document.getElementById('auth-panel');
const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const authSubmit = document.getElementById('auth-submit');
const authToggle = document.getElementById('auth-toggle');
const authError = document.getElementById('auth-error');
const dashboard = document.getElementById('dashboard');
const dashboardError = document.getElementById('dashboard-error');
const plantForm = document.getElementById('plant-form');
const plantSelect = document.getElementById('plant-select');
const plantDetails = document.getElementById('plant-details');
const manualForm = document.getElementById('manual-form');
const historyRows = document.getElementById('history-rows');

let authMode = 'login';
let token = localStorage.getItem('materaToken');
let email = localStorage.getItem('materaEmail') || '';
let plants = [];
let selectedPlantId = '';
let polling = false;
let pollTimer;

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function mostrarMensaje(elemento, mensaje) {
  elemento.textContent = mensaje;
  elemento.classList.toggle('hidden', !mensaje);
}

function limpiarMensaje(elemento) {
  mostrarMensaje(elemento, '');
}

async function apiRequest(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError('La API devolvió una respuesta inválida.', response.status);
    }
  }
  if (!response.ok) {
    throw new ApiError(data.error || 'No se pudo completar la solicitud.', response.status);
  }
  return data;
}

function cambiarModoAutenticacion() {
  authMode = authMode === 'login' ? 'registro' : 'login';
  const registrando = authMode === 'registro';
  authTitle.textContent = registrando ? 'Crea tu cuenta' : 'Inicia sesión';
  authSubmit.textContent = registrando ? 'Registrarme' : 'Iniciar sesión';
  authToggle.textContent = registrando
    ? '¿Ya tienes cuenta? Inicia sesión'
    : '¿No tienes cuenta? Regístrate';
  document.getElementById('contrasena').autocomplete = registrando
    ? 'new-password'
    : 'current-password';
  limpiarMensaje(authError);
}

function cerrarSesion(mensaje = '') {
  localStorage.removeItem('materaToken');
  localStorage.removeItem('materaEmail');
  token = '';
  email = '';
  plants = [];
  selectedPlantId = '';
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = undefined;
  }
  dashboard.classList.add('hidden');
  authPanel.classList.remove('hidden');
  document.getElementById('device-credentials').classList.add('hidden');
  document.getElementById('device-id').textContent = '';
  document.getElementById('device-token').textContent = '';
  mostrarMensaje(authError, mensaje);
}

async function iniciarSesion(data) {
  token = data.token;
  email = data.usuario.email;
  localStorage.setItem('materaToken', token);
  localStorage.setItem('materaEmail', email);
  authPanel.classList.add('hidden');
  dashboard.classList.remove('hidden');
  document.getElementById('welcome-message').textContent = `Sesión de ${email}`;
  limpiarMensaje(authError);
  limpiarMensaje(dashboardError);
  await cargarEspecies();
  await cargarPlantas();
  if (!pollTimer) {
    pollTimer = setInterval(() => {
      actualizarMonitor().catch((error) => mostrarErrorPanel(error));
    }, POLL_INTERVAL_MS);
  }
}

async function cargarEspecies() {
  const data = await apiRequest('/especies');
  const select = document.getElementById('plant-species');
  select.replaceChildren(new Option('Selecciona una especie', ''));
  data.especies.forEach((especie) => {
    select.appendChild(new Option(especie, especie));
  });
}

async function cargarPlantas() {
  const data = await apiRequest('/plantas');
  plants = data.plantas;
  plantSelect.replaceChildren();
  if (plants.length === 0) {
    plantSelect.appendChild(new Option('Aún no tienes plantas', ''));
    selectedPlantId = '';
    plantDetails.classList.add('hidden');
    document.getElementById('poll-status').textContent = 'Agrega una planta para comenzar.';
    return;
  }

  plants.forEach((planta) => {
    plantSelect.appendChild(new Option(`${planta.nombre} · ${planta.especie}`, planta.id));
  });
  if (!plants.some((planta) => planta.id === selectedPlantId)) {
    selectedPlantId = plants[0].id;
  }
  plantSelect.value = selectedPlantId;
  await actualizarMonitor();
}

function mostrarErrorPanel(error) {
  if (error.status === 401 && token) {
    cerrarSesion('Tu sesión venció. Inicia sesión nuevamente.');
    return;
  }
  mostrarMensaje(dashboardError, error.message || 'No se pudo consultar la API.');
}

async function actualizarMonitor() {
  if (polling || !selectedPlantId) {
    return;
  }
  polling = true;
  const planta = plants.find((item) => item.id === selectedPlantId);
  if (!planta) {
    polling = false;
    return;
  }

  try {
    document.getElementById('poll-status').textContent = 'Actualizando...';
    document.getElementById('plant-title').textContent = planta.nombre;
    plantDetails.classList.remove('hidden');

    const diagnostico = await apiRequest(
      `/plantas/${encodeURIComponent(planta.id)}/estado`,
    );
    const historial = await apiRequest(
      `/plantas/${encodeURIComponent(planta.id)}/lecturas`,
    );
    mostrarDiagnostico(diagnostico);
    mostrarHistorial(historial.lecturas);
    document.getElementById('poll-status').textContent =
      `Actualizado automáticamente · cada ${POLL_INTERVAL_MS / 1000} s`;
    limpiarMensaje(dashboardError);
  } finally {
    polling = false;
  }
}

function mostrarDiagnostico(data) {
  const badge = document.getElementById('estado-badge');
  const listaParametros = document.getElementById('lista-parametros');
  const listaRecomendaciones = document.getElementById('lista-recomendaciones');
  listaParametros.replaceChildren();
  listaRecomendaciones.replaceChildren();

  if (!data || data.estado === 'SIN_LECTURAS') {
    badge.textContent = 'Sin lecturas';
    badge.style.backgroundColor = '#f3f4f6';
    document.getElementById('last-reading').textContent =
      'El dispositivo aún no ha reportado; puedes registrar una lectura manual.';
    return;
  }

  badge.textContent = data.estado;
  const badgeColors = {
    SALUDABLE: '#e8f5e9',
    EN_RIESGO: '#fff8e1',
    CRITICO: '#ffebee',
  };
  badge.style.backgroundColor = badgeColors[data.estado] || '#f3f4f6';
  data.parametros.forEach((parametro) => {
    const item = document.createElement('li');
    item.textContent =
      `${parametro.nombre}: ${parametro.valor} ${parametro.unidad} · ${parametro.estado} ` +
      `(rango ${parametro.rango_min}–${parametro.rango_max})`;
    listaParametros.appendChild(item);
  });
  if (data.recomendaciones.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'La planta está en su rango ideal.';
    listaRecomendaciones.appendChild(item);
  } else {
    data.recomendaciones.forEach((recomendacion) => {
      const item = document.createElement('li');
      item.textContent = recomendacion;
      listaRecomendaciones.appendChild(item);
    });
  }
  document.getElementById('last-reading').textContent = 'Estado calculado con la lectura más reciente.';
}

function mostrarHistorial(lecturas) {
  historyRows.replaceChildren();
  document.getElementById('empty-history').classList.toggle('hidden', lecturas.length > 0);
  lecturas.forEach((lectura) => {
    const fila = document.createElement('tr');
    const fecha = new Date(lectura.marca_temporal).toLocaleString();
    [fecha, lectura.origen, `${lectura.humedad} %`, `${lectura.luz} lux`, `${lectura.temperatura} °C`]
      .forEach((valor) => {
        const celda = document.createElement('td');
        celda.textContent = valor;
        fila.appendChild(celda);
      });
    historyRows.appendChild(fila);
  });
}

authForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  limpiarMensaje(authError);
  const credenciales = {
    email: document.getElementById('email').value.trim(),
    contrasena: document.getElementById('contrasena').value,
  };
  const ruta = authMode === 'registro' ? '/auth/registro' : '/auth/login';
  try {
    await iniciarSesion(await apiRequest(ruta, {
      method: 'POST',
      body: JSON.stringify(credenciales),
    }));
  } catch (error) {
    if (token) {
      mostrarErrorPanel(error);
    } else {
      mostrarMensaje(authError, error.message);
    }
  }
});

authToggle.addEventListener('click', cambiarModoAutenticacion);

document.getElementById('logout-button').addEventListener('click', () => cerrarSesion());

plantForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  limpiarMensaje(dashboardError);
  try {
    const planta = await apiRequest('/plantas', {
      method: 'POST',
      body: JSON.stringify({
        nombre: document.getElementById('plant-name').value.trim(),
        especie: document.getElementById('plant-species').value,
      }),
    });
    document.getElementById('device-id').textContent = planta.dispositivo_id;
    document.getElementById('device-token').textContent = planta.token_dispositivo;
    document.getElementById('device-credentials').classList.remove('hidden');
    plantForm.reset();
    await cargarPlantas();
  } catch (error) {
    mostrarErrorPanel(error);
  }
});

plantSelect.addEventListener('change', () => {
  selectedPlantId = plantSelect.value;
  actualizarMonitor().catch((error) => mostrarErrorPanel(error));
});

manualForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const planta = plants.find((item) => item.id === selectedPlantId);
  if (!planta) {
    mostrarMensaje(dashboardError, 'Selecciona una planta primero.');
    return;
  }
  try {
    await apiRequest(`/plantas/${encodeURIComponent(planta.id)}/lecturas`, {
      method: 'POST',
      body: JSON.stringify({
        especie: planta.especie,
        humedad: Number(document.getElementById('humedad').value),
        luz: Number(document.getElementById('luz').value),
        temperatura: Number(document.getElementById('temperatura').value),
      }),
    });
    manualForm.reset();
    await actualizarMonitor();
  } catch (error) {
    mostrarErrorPanel(error);
  }
});

document.getElementById('copy-device-token').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(document.getElementById('device-token').textContent);
    mostrarMensaje(dashboardError, 'Token copiado. Guárdalo para iniciar el simulador.');
  } catch {
    mostrarMensaje(dashboardError, 'No se pudo copiar; selecciona el token y cópialo manualmente.');
  }
});

if (token) {
  iniciarSesion({ token, usuario: { email } }).catch((error) => {
    cerrarSesion(error.message || 'No se pudo recuperar la sesión.');
  });
}
