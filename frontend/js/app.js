const API_URL = 'http://127.0.0.1:5000/api/v1';
const POLL_INTERVAL_MS = 5000;
const DISCONNECTED_AFTER_MS = 60_000;
const ALERTS_STORAGE_KEY = 'materaAlerts';

const authPanel = document.getElementById('auth-panel');
const appShell = document.getElementById('app-shell');
const authForm = document.getElementById('auth-form');
const authError = document.getElementById('auth-error');
const authTitle = document.getElementById('auth-title');
const authSubtitle = document.getElementById('auth-subtitle');
const authSubmit = document.getElementById('auth-submit');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const addPlantDialog = document.getElementById('add-plant-dialog');
const noticeDialog = document.getElementById('notice-dialog');
const plantGrid = document.getElementById('plant-grid');
const allPlantsGrid = document.getElementById('all-plants-grid');
const historyRows = document.getElementById('history-rows');

let token = localStorage.getItem('materaToken') || sessionStorage.getItem('materaToken') || '';
let userEmail = localStorage.getItem('materaEmail') || '';
let displayName = localStorage.getItem('materaName') || '';
let authMode = 'login';
let plants = [];
let species = [];
let selectedPlantId = '';
let currentView = 'dashboard';
let isRefreshing = false;
let pollTimer;
let dashboardFilter = 'Todas';
let plantsFilter = 'Todas';
let alertFilter = 'all';
let historyPeriod = '1';
let historySource = 'all';
let historyFilteredReadings = [];
let unreadAlerts = 0;
let alerts = readStoredAlerts();
let deviceCredentials = null;
let lastStatuses = new Map();

class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.status = status;
  }
}

function readStoredAlerts() {
  try {
    const parsed = JSON.parse(localStorage.getItem(alertsStorageKey()) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function storeAlerts() {
  if (userEmail) {
    localStorage.setItem(alertsStorageKey(), JSON.stringify(alerts));
  }
}

function alertsStorageKey() {
  return `${ALERTS_STORAGE_KEY}:${userEmail.trim().toLocaleLowerCase('es')}`;
}

async function apiRequest(path, options = {}) {
  const { token: requestToken, ...fetchOptions } = options;
  const headers = { ...(fetchOptions.headers || {}) };
  if (requestToken || token) {
    headers.Authorization = `Bearer ${requestToken || token}`;
  }
  if (fetchOptions.body) {
    headers['Content-Type'] = 'application/json';
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers });
  } catch {
    throw new ApiError('No se pudo conectar con el servidor. Comprueba que la API esté activa.');
  }

  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError('El servidor devolvió una respuesta que no es JSON.', response.status);
    }
  }
  if (!response.ok) {
    throw new ApiError(data.error || 'No se pudo completar la solicitud.', response.status);
  }
  return data;
}

function element(tag, className = '', text = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function showMessage(node, message, style = 'error') {
  node.textContent = message;
  node.classList.toggle('hidden', !message);
  node.classList.toggle('is-success', style === 'success' && Boolean(message));
}

function selectedPlant() {
  return plants.find((plant) => plant.id === selectedPlantId) || null;
}

function statusOf(plant) {
  return plant?.connected ? plant.diagnosis?.estado || 'SIN_LECTURAS' : 'DESCONECTADA';
}

function prettyStatus(status) {
  return {
    SALUDABLE: 'Saludable',
    EN_RIESGO: 'En riesgo',
    CRITICO: 'Crítico',
    DESCONECTADA: 'Desconectada',
    SIN_LECTURAS: 'Sin lecturas',
  }[status] || status;
}

function statusClass(status) {
  return {
    SALUDABLE: 'healthy',
    EN_RIESGO: 'risk',
    CRITICO: 'critical',
    DESCONECTADA: 'offline',
    SIN_LECTURAS: 'offline',
  }[status] || 'offline';
}

function plantIllustration(speciesName = '') {
  const name = speciesName.toLowerCase();
  if (name.includes('sansevieria')) return '🪴';
  if (name.includes('potos')) return '🌿';
  if (name.includes('suculenta')) return '🌵';
  if (name.includes('helecho')) return '🌱';
  if (name.includes('lavanda')) return '🪻';
  if (name.includes('manito')) return '🌼';
  return '🪴';
}

function formatDate(value, options = {}) {
  if (!value) return 'Sin registros';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Fecha desconocida';
  return new Intl.DateTimeFormat('es', {
    dateStyle: options.dateStyle || 'medium',
    ...(options.time ? { timeStyle: 'short' } : {}),
  }).format(date);
}

function relativeTime(value) {
  if (!value) return 'Aún no hay lecturas';
  const elapsed = Math.max(0, Date.now() - new Date(value).getTime());
  if (elapsed < 60_000) return `Hace ${Math.max(1, Math.floor(elapsed / 1000))} s`;
  if (elapsed < 3_600_000) return `Hace ${Math.floor(elapsed / 60_000)} min`;
  if (elapsed < 86_400_000) return `Hace ${Math.floor(elapsed / 3_600_000)} h`;
  return formatDate(value);
}

function setAuthMode(mode) {
  authMode = mode;
  const isRegistering = mode === 'register';
  loginTab.classList.toggle('is-active', !isRegistering);
  registerTab.classList.toggle('is-active', isRegistering);
  loginTab.setAttribute('aria-selected', String(!isRegistering));
  registerTab.setAttribute('aria-selected', String(isRegistering));
  document.getElementById('name-field').classList.toggle('hidden', !isRegistering);
  document.getElementById('confirm-field').classList.toggle('hidden', !isRegistering);
  document.getElementById('login-options').classList.toggle('hidden', isRegistering);
  document.getElementById('auth-name').required = isRegistering;
  document.getElementById('confirm-password').required = isRegistering;
  document.getElementById('contrasena').autocomplete = isRegistering ? 'new-password' : 'current-password';
  authTitle.textContent = isRegistering ? 'Crea tu cuenta' : 'Qué bueno verte';
  authSubtitle.textContent = isRegistering
    ? 'Empieza un jardín lleno de vida.'
    : 'Inicia sesión para ver cómo están tus plantas.';
  authSubmit.innerHTML = isRegistering
    ? 'Crear mi cuenta <span aria-hidden="true">→</span>'
    : 'Iniciar sesión <span aria-hidden="true">→</span>';
  showMessage(authError, '');
}

function showNotice(title, message) {
  document.getElementById('notice-title').textContent = title;
  document.getElementById('notice-message').textContent = message;
  noticeDialog.showModal();
}

function onApiError(error, target = null) {
  if (error.status === 401 && token) {
    signOut('Tu sesión terminó. Inicia sesión nuevamente.');
    return;
  }
  if (target) showMessage(target, error.message);
}

async function authenticate(event) {
  event.preventDefault();
  showMessage(authError, '');
  const password = document.getElementById('contrasena').value;
  const credentials = {
    email: document.getElementById('email').value.trim(),
    contrasena: password,
  };

  if (authMode === 'register') {
    const confirmation = document.getElementById('confirm-password').value;
    if (password !== confirmation) {
      showMessage(authError, 'Las contraseñas no coinciden.');
      return;
    }
    displayName = document.getElementById('auth-name').value.trim();
  }

  authSubmit.disabled = true;
  try {
    const route = authMode === 'register' ? '/auth/registro' : '/auth/login';
    const result = await apiRequest(route, {
      method: 'POST',
      body: JSON.stringify(credentials),
      token: '',
    });
    token = result.token;
    userEmail = result.usuario.email;
    const remember = document.getElementById('remember-me').checked;
    localStorage.removeItem('materaToken');
    sessionStorage.removeItem('materaToken');
    (remember ? localStorage : sessionStorage).setItem('materaToken', token);
    localStorage.setItem('materaEmail', userEmail);
    localStorage.setItem('materaName', displayName);
    await enterApplication();
  } catch (error) {
    showMessage(authError, error.message);
  } finally {
    authSubmit.disabled = false;
  }
}

async function enterApplication() {
  authPanel.classList.add('hidden');
  appShell.classList.remove('hidden');
  document.body.classList.add('is-authenticated');
  navigate('dashboard');
  const name = displayName || userEmail.split('@')[0] || 'Jardinero';
  document.getElementById('sidebar-user').textContent = name;
  document.getElementById('header-user').textContent = name;
  document.getElementById('greeting-name').textContent = name;
  document.getElementById('shared-owner-name').textContent = name;
  document.getElementById('settings-email').textContent = userEmail;
  document.getElementById('today-date').textContent = new Intl.DateTimeFormat('es', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date()).toUpperCase();
  alerts = readStoredAlerts();

  await loadSpecies();
  await refreshGarden();
  if (!pollTimer) {
    pollTimer = setInterval(() => {
      refreshGarden().catch((error) => {
        if (error.status === 401) {
          signOut('Tu sesión terminó. Inicia sesión nuevamente.');
        } else {
          showMessage(document.getElementById('global-error'), error.message);
        }
      });
    }, POLL_INTERVAL_MS);
  }
}

async function loadSpecies() {
  const data = await apiRequest('/especies');
  species = data.especies;
  ['new-plant-species', 'manual-species'].forEach((id) => {
    const select = document.getElementById(id);
    select.replaceChildren();
    if (id === 'new-plant-species') {
      select.appendChild(new Option('Selecciona una especie', ''));
    }
    species.forEach((name) => select.appendChild(new Option(name, name)));
  });
}

async function refreshGarden() {
  if (isRefreshing || !token) return;
  isRefreshing = true;
  try {
    const response = await apiRequest('/plantas');
    const plantsBefore = plants;
    const refreshed = await Promise.all(response.plantas.map(async (plant) => {
      const [diagnosis, history] = await Promise.all([
        apiRequest(`/plantas/${encodeURIComponent(plant.id)}/estado`),
        apiRequest(`/plantas/${encodeURIComponent(plant.id)}/lecturas`),
      ]);
      const readings = history.lecturas || [];
      const latest = readings[0] || null;
      const connected = Boolean(
        latest && Date.now() - new Date(latest.marca_temporal).getTime() <= DISCONNECTED_AFTER_MS,
      );
      return { ...plant, diagnosis, readings, latest, connected };
    }));

    plants = refreshed;
    showMessage(document.getElementById('global-error'), '');
    if (!plants.some((plant) => plant.id === selectedPlantId)) {
      selectedPlantId = plants[0]?.id || '';
    }
    trackStatusChanges(plantsBefore, plants);
    renderGarden();
    if (currentView === 'detail' || currentView === 'history' || currentView === 'manual' || currentView === 'shared') {
      renderSelectedPlant();
    }
  } finally {
    isRefreshing = false;
  }
}

function trackStatusChanges(previousPlants, currentPlants) {
  const previous = new Map(previousPlants.map((plant) => [plant.id, statusOf(plant)]));
  currentPlants.forEach((plant) => {
    const next = statusOf(plant);
    const old = previous.get(plant.id) || lastStatuses.get(plant.id);
    if (old && old !== next && next !== 'SIN_LECTURAS') {
      addAlert(plant, next, `El estado de ${plant.nombre} cambió a ${prettyStatus(next).toLowerCase()}.`);
    }
    lastStatuses.set(plant.id, next);
  });
}

function addAlert(plant, status, message) {
  alerts.unshift({
    id: `${plant.id}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    plantId: plant.id,
    plantName: plant.nombre,
    status,
    message,
    createdAt: new Date().toISOString(),
    read: false,
  });
  alerts = alerts.slice(0, 100);
  storeAlerts();
}

function renderGarden() {
  renderStats();
  document.getElementById('plant-total').textContent = plants.length;
  document.getElementById('nav-plant-count').textContent = plants.length;
  document.getElementById('settings-plant-count').textContent = plants.length;
  document.getElementById('garden-summary').textContent = plants.length
    ? '¡Tu jardín está creciendo!'
    : '¡Tu jardín está a salvo!';
  const connected = plants.filter((plant) => plant.connected).length;
  document.getElementById('garden-subsummary').textContent = plants.length
    ? `${connected} ${connected === 1 ? 'planta conectada' : 'plantas conectadas'} · ${plants.length - connected} esperando una lectura.`
    : 'Agrega tu primera planta y empieza a cuidarla.';
  document.getElementById('dashboard-empty').classList.toggle('hidden', plants.length > 0);
  renderPlantCards(plantGrid, dashboardFilter, '');
  renderPlantCards(allPlantsGrid, plantsFilter, document.getElementById('plant-search').value);
  renderRecentActivity();
  renderAlerts();
  updateAlertCounters();
  updatePlantSelectors();
  renderSelectedPlant();
}

function renderStats() {
  const counts = {
    SALUDABLE: plants.filter((plant) => statusOf(plant) === 'SALUDABLE').length,
    EN_RIESGO: plants.filter((plant) => statusOf(plant) === 'EN_RIESGO').length,
    CRITICO: plants.filter((plant) => statusOf(plant) === 'CRITICO').length,
    DESCONECTADA: plants.filter((plant) => statusOf(plant) === 'DESCONECTADA' || statusOf(plant) === 'SIN_LECTURAS').length,
  };
  const stats = [
    ['SALUDABLE', 'Todo bien', '☀', counts.SALUDABLE],
    ['EN_RIESGO', 'Necesita atención', '♧', counts.EN_RIESGO],
    ['CRITICO', 'Prioridad', '♡', counts.CRITICO],
    ['DESCONECTADA', 'Sin conexión', '⌁', counts.DESCONECTADA],
  ];
  const root = document.getElementById('stats-grid');
  root.replaceChildren(...stats.map(([status, title, icon, count]) => {
    const card = element('button', `stat-card ${statusClass(status)}`);
    card.type = 'button';
    card.dataset.filter = status;
    const iconNode = element('span', 'stat-icon', icon);
    const text = element('span', 'stat-copy');
    text.append(element('span', 'stat-label', title), element('strong', 'stat-number', String(count)));
    card.append(iconNode, text, element('span', 'stat-arrow', '↗'));
    return card;
  }));
}

function filteredPlants(filter, search = '') {
  const needle = search.trim().toLocaleLowerCase('es');
  return plants.filter((plant) => {
    const state = statusOf(plant);
    const matchesFilter = filter === 'Todas'
      || state === filter
      || (filter === 'DESCONECTADA' && state === 'SIN_LECTURAS');
    const matchesSearch = !needle
      || `${plant.nombre} ${plant.especie}`.toLocaleLowerCase('es').includes(needle);
    return matchesFilter && matchesSearch;
  });
}

function makePlantCard(plant) {
  const status = statusOf(plant);
  const card = element('button', `plant-card ${statusClass(status)}`);
  card.type = 'button';
  card.dataset.plantId = plant.id;
  card.setAttribute('aria-label', `Ver ${plant.nombre}, ${prettyStatus(status)}`);

  const cover = element('span', 'plant-art');
  const art = element('span', 'plant-emoji', plantIllustration(plant.especie));
  cover.append(art);
  const online = element('span', `online-indicator ${plant.connected ? 'is-online' : ''}`);
  online.setAttribute('aria-label', plant.connected ? 'Conectada' : 'Desconectada');
  cover.append(online);

  const body = element('span', 'plant-card-body');
  const titleRow = element('span', 'plant-card-title');
  titleRow.append(element('strong', '', plant.nombre), element('span', 'card-chevron', '↗'));
  body.append(titleRow, element('span', 'plant-species', plant.especie));

  const badge = element('span', `status-badge ${statusClass(status)}`);
  badge.append(element('i', 'status-dot'), document.createTextNode(prettyStatus(status)));
  body.append(badge);

  if (plant.latest) {
    const metrics = element('span', 'plant-card-metrics');
    [
      ['Humedad', `${plant.latest.humedad}%`, '♧'],
      ['Luz', `${plant.latest.luz} lux`, '☼'],
      ['Temp.', `${plant.latest.temperatura}°`, '♨'],
    ].forEach(([label, value, icon]) => {
      const metric = element('span', 'plant-card-metric');
      metric.append(element('i', '', icon), element('small', '', label), element('strong', '', value));
      metrics.append(metric);
    });
    body.append(metrics);
    body.append(element('span', 'card-last-seen', `${plant.connected ? 'Conectada' : 'Última lectura'} · ${relativeTime(plant.latest.marca_temporal)}`));
  } else {
    body.append(element('span', 'card-last-seen', 'Esperando su primera lectura'));
  }
  card.append(cover, body);
  card.addEventListener('click', () => {
    selectedPlantId = plant.id;
    navigate('detail');
    renderSelectedPlant();
  });
  return card;
}

function renderPlantCards(container, filter, search) {
  const filtered = filteredPlants(filter, search);
  container.replaceChildren(...filtered.map(makePlantCard));
  const empty = element('div', 'empty-inline');
  empty.append(element('span', '', '🪴'), element('strong', '', search || filter !== 'Todas' ? 'No encontramos plantas con ese filtro.' : 'Agrega tu primera planta.'));
  if (container === allPlantsGrid) {
    container.classList.toggle('hidden', plants.length === 0);
    if (!filtered.length && plants.length) container.append(empty);
  } else if (!filtered.length && plants.length) {
    container.append(empty);
  }
}

function updatePlantSelectors() {
  const selectedHistory = document.getElementById('history-plant').value || selectedPlantId;
  const selectedShared = document.getElementById('shared-plant-select').value || selectedPlantId;
  const selectedAlert = document.getElementById('alert-plant-filter').value || 'all';
  [
    ['history-plant', false, selectedHistory],
    ['shared-plant-select', false, selectedShared],
    ['alert-plant-filter', true, selectedAlert],
  ].forEach(([id, includeAll, previous]) => {
    const select = document.getElementById(id);
    select.replaceChildren();
    if (includeAll) select.appendChild(new Option('Todas las plantas', 'all'));
    plants.forEach((plant) => select.appendChild(new Option(plant.nombre, plant.id)));
    select.value = plants.some((plant) => plant.id === previous) || (includeAll && previous === 'all')
      ? previous
      : (includeAll ? 'all' : (plants[0]?.id || ''));
  });
}

function renderSelectedPlant() {
  const plant = selectedPlant();
  if (!plant) {
    if (currentView === 'detail') navigate('plants');
    document.getElementById('metric-gauges').replaceChildren();
    return;
  }
  document.getElementById('detail-title').textContent = plant.nombre;
  document.getElementById('detail-species').textContent = plant.especie;
  document.getElementById('detail-plant-art').textContent = plantIllustration(plant.especie);
  document.getElementById('about-species').textContent = plant.especie;
  document.getElementById('about-device').textContent = plant.device_id || 'ESP32';
  document.getElementById('about-readings').textContent = String(plant.readings.length);
  document.getElementById('shared-plant-name').textContent = plant.nombre;
  document.getElementById('shared-plant-species').textContent = plant.especie;
  document.getElementById('shared-plant-art').textContent = plantIllustration(plant.especie);
  document.getElementById('history-plant').value = plant.id;
  document.getElementById('shared-plant-select').value = plant.id;

  const status = statusOf(plant);
  const connectionBanner = document.getElementById('connection-banner');
  connectionBanner.classList.toggle('is-disconnected', !plant.connected);
  connectionBanner.replaceChildren(
    element('span', 'connection-symbol', plant.connected ? '●' : '⌁'),
    element('span', '', plant.connected
      ? `Conectada · última lectura ${relativeTime(plant.latest?.marca_temporal)}`
      : `Sin conexión${plant.latest ? ` · última lectura ${relativeTime(plant.latest.marca_temporal)}` : ' · aún no llegan lecturas'}. Mostrando el registro manual.`),
  );
  document.getElementById('manual-disconnected-banner').textContent = plant.connected
    ? `Puedes guardar una lectura manual de ${plant.nombre} cuando quieras.`
    : `${plant.nombre} no tiene conexión con el sensor. Puedes ingresar valores manualmente.`;
  document.getElementById('manual-species').value = plant.especie;
  document.getElementById('detail-connection').replaceChildren(
    element('i', `online-indicator ${plant.connected ? 'is-online' : ''}`),
    element('span', '', plant.connected ? 'Conectada' : 'Desconectada'),
    element('span', 'muted', plant.latest ? `· ${relativeTime(plant.latest.marca_temporal)}` : '· Sin lecturas'),
  );
  const stateHero = document.getElementById('detail-state');
  stateHero.className = `state-hero ${statusClass(status)}`;
  stateHero.replaceChildren(element('span', 'state-hero-label', prettyStatus(status)), element('small', '', 'Índice de vitalidad'));
  document.getElementById('detail-reading-time').textContent = plant.latest
    ? `Actualizado ${relativeTime(plant.latest.marca_temporal)}`
    : 'Aún no hay datos del sensor';

  renderGauges(plant);
  renderRecommendations(plant);
  document.getElementById('mini-chart').innerHTML = makeChart(plant.readings.slice(0, 24).reverse(), 'mini');
  renderHistory();
}

function renderGauges(plant) {
  const root = document.getElementById('metric-gauges');
  root.replaceChildren();
  const diagnosisParams = new Map((plant.diagnosis?.parametros || []).map((item) => [item.nombre, item]));
  const definitions = [
    ['humedad', 'Humedad', '%', 100, '♧'],
    ['luz', 'Luz', 'lux', 3000, '☼'],
    ['temperatura', 'Temperatura', '°C', 50, '♨'],
  ];
  definitions.forEach(([key, title, unit, maximum, icon]) => {
    const reading = plant.latest?.[key];
    const parameter = diagnosisParams.get(key);
    const normalized = reading == null ? 0 : Math.max(0, Math.min(100, (reading / maximum) * 100));
    const card = element('article', `metric-card ${parameter ? statusClass(parameter.estado === 'OPTIMO' ? 'SALUDABLE' : 'EN_RIESGO') : ''}`);
    const top = element('span', 'metric-card-top');
    top.append(element('span', 'metric-icon', icon), element('span', 'metric-title', title));
    const gauge = element('span', 'gauge');
    gauge.style.setProperty('--gauge-value', `${normalized}%`);
    gauge.append(element('span', 'gauge-value', reading == null ? '—' : String(reading)));
    card.append(top, gauge, element('span', 'metric-unit', unit));
    const state = parameter?.estado || (reading == null ? 'SIN_LECTURAS' : 'OPTIMO');
    const label = element('span', `metric-state ${state === 'OPTIMO' ? 'healthy' : state === 'SIN_LECTURAS' ? 'offline' : 'risk'}`, state === 'OPTIMO' ? 'ÓPTIMO' : state === 'SIN_LECTURAS' ? 'SIN DATOS' : state);
    card.append(label);
    if (parameter) card.append(element('span', 'metric-range', `Ideal ${parameter.rango_min}–${parameter.rango_max} ${unit}`));
    root.append(card);
  });
}

function renderRecommendations(plant) {
  const list = document.getElementById('detail-recommendations');
  const items = plant.diagnosis?.recomendaciones || [];
  list.replaceChildren();
  if (!items.length) {
    list.append(element('li', 'recommendation-item is-positive', 'Tu planta está en su rango ideal. ¡Sigue así!'));
    return;
  }
  items.forEach((text) => {
    const item = element('li', 'recommendation-item');
    item.append(element('span', 'recommendation-icon', '✦'), element('span', '', text));
    list.append(item);
  });
}

function renderHistory() {
  const plant = selectedPlant();
  const readings = plant?.readings || [];
  const now = Date.now();
  const cutoff = historyPeriod === 'all' ? 0 : now - Number(historyPeriod) * 86_400_000;
  historyFilteredReadings = readings.filter((reading) => {
    const date = new Date(reading.marca_temporal).getTime();
    return date >= cutoff && (historySource === 'all' || reading.origen === historySource);
  });
  renderHistorySummary(historyFilteredReadings);
  document.getElementById('history-count').textContent = historyFilteredReadings.length;
  document.getElementById('history-empty').classList.toggle('hidden', historyFilteredReadings.length > 0);
  document.querySelector('.history-chart-section').classList.toggle('hidden', !historyFilteredReadings.length);
  document.querySelector('.history-table').classList.toggle('hidden', !historyFilteredReadings.length);
  document.getElementById('history-chart').innerHTML = makeChart(historyFilteredReadings.slice(0, 100).reverse(), 'history');
  historyRows.replaceChildren(...historyFilteredReadings.map((reading, index) => makeHistoryRow(reading, index)));
}

function renderHistorySummary(readings) {
  const root = document.getElementById('history-summary');
  root.replaceChildren();
  [
    ['humedad', 'Humedad promedio', '%', 'humidity'],
    ['luz', 'Luz promedio', 'lux', 'light'],
    ['temperatura', 'Temperatura promedio', '°C', 'temperature'],
  ].forEach(([key, label, unit, tone]) => {
    const average = readings.length
      ? readings.reduce((sum, reading) => sum + Number(reading[key]), 0) / readings.length
      : null;
    const card = element('article', `summary-stat ${tone}`);
    card.append(element('span', 'summary-icon', key === 'humedad' ? '♧' : key === 'luz' ? '☼' : '♨'));
    const copy = element('span', '');
    copy.append(element('small', '', label), element('strong', '', average == null ? '—' : `${average.toFixed(1)} ${unit}`), element('small', 'summary-hint', readings.length ? `${readings.length} mediciones` : 'Sin datos'));
    card.append(copy);
    root.append(card);
  });
}

function makeHistoryRow(reading) {
  const row = element('tr');
  const status = getReadingStatus(reading);
  const values = [
    formatDate(reading.marca_temporal, { time: true }),
    reading.origen,
    `${reading.humedad} %`,
    `${reading.luz} lux`,
    `${reading.temperatura} °C`,
  ];
  values.forEach((value, index) => {
    const cell = element('td');
    if (index === 1) {
      cell.append(element('span', `source-badge ${reading.origen === 'SENSOR' ? 'sensor' : 'manual'}`, reading.origen === 'SENSOR' ? '⌁ Sensor' : '✎ Manual'));
    } else {
      cell.textContent = value;
    }
    row.append(cell);
  });
  const stateCell = element('td');
  const badge = element('span', `status-badge ${statusClass(status)}`);
  badge.append(element('i', 'status-dot'), document.createTextNode(prettyStatus(status)));
  stateCell.append(badge);
  row.append(stateCell);
  return row;
}

function getReadingStatus(reading) {
  const params = selectedPlant()?.diagnosis?.parametros || [];
  if (!params.length) return 'SIN_LECTURAS';
  const outside = params.filter((parameter) => {
    const value = Number(reading[parameter.nombre]);
    return value < parameter.rango_min || value > parameter.rango_max;
  }).length;
  return outside === 0 ? 'SALUDABLE' : outside === 1 ? 'EN_RIESGO' : 'CRITICO';
}

function makeChart(readings, id) {
  if (!readings.length) {
    return '<div class="chart-empty"><span>🌱</span><strong>Aún no hay lecturas</strong><p>Los datos aparecerán aquí cuando tu planta reporte.</p></div>';
  }
  const width = 760;
  const height = 220;
  const pad = { top: 18, right: 18, bottom: 28, left: 36 };
  const graphWidth = width - pad.left - pad.right;
  const graphHeight = height - pad.top - pad.bottom;
  const values = [
    { key: 'humedad', color: '#55a879', max: 100 },
    { key: 'luz', color: '#e9ad48', max: Math.max(3000, ...readings.map((item) => Number(item.luz))) },
    { key: 'temperatura', color: '#e98272', max: 50 },
  ];
  const grid = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const y = pad.top + graphHeight * fraction;
    return `<line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="#e9eee6" stroke-dasharray="3 5"/><text x="${pad.left - 10}" y="${y + 4}" text-anchor="end" fill="#9aa69b" font-size="10">${Math.round((1 - fraction) * 100)}</text>`;
  }).join('');
  const paths = values.map(({ key, color, max }) => {
    const points = readings.map((reading, index) => {
      const x = pad.left + (readings.length === 1 ? graphWidth / 2 : (index / (readings.length - 1)) * graphWidth);
      const normalized = Math.max(0, Math.min(1, Number(reading[key]) / max));
      const y = pad.top + graphHeight * (1 - normalized);
      return { x, y, reading };
    });
    const d = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
    const line = `<path d="${d}" fill="none" stroke="${color}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>`;
    const dots = points.map(({ x, y, reading }) => `<circle cx="${x}" cy="${y}" r="3.7" fill="#fff" stroke="${color}" stroke-width="2"><title>${escapeHtml(formatDate(reading.marca_temporal, { time: true }))} · ${key}: ${escapeHtml(reading[key])}</title></circle>`).join('');
    return `${line}${dots}`;
  }).join('');
  const labelIndexes = [...new Set([0, Math.floor((readings.length - 1) / 2), readings.length - 1])];
  const labels = labelIndexes.map((index) => {
    const x = pad.left + (readings.length === 1 ? graphWidth / 2 : (index / (readings.length - 1)) * graphWidth);
    const date = new Date(readings[index].marca_temporal);
    const label = Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
    return `<text x="${x}" y="${height - 4}" text-anchor="middle" fill="#9aa69b" font-size="10">${escapeHtml(label)}</text>`;
  }).join('');
  return `<svg class="line-chart ${id}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Gráfica de tendencias de humedad, luz y temperatura">${grid}${paths}${labels}</svg>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

function renderRecentActivity() {
  const list = document.getElementById('recent-activity');
  const recent = plants.flatMap((plant) => plant.readings.slice(0, 1).map((reading) => ({ plant, reading })))
    .sort((left, right) => new Date(right.reading.marca_temporal) - new Date(left.reading.marca_temporal))
    .slice(0, 4);
  list.replaceChildren();
  if (!recent.length) {
    list.append(element('p', 'muted', 'Aquí aparecerán las últimas lecturas de tu jardín.'));
    return;
  }
  recent.forEach(({ plant, reading }) => {
    const item = element('button', 'activity-row');
    item.type = 'button';
    item.append(element('span', 'activity-icon', reading.origen === 'SENSOR' ? '⌁' : '✎'));
    const copy = element('span', 'activity-copy');
    copy.append(element('strong', '', plant.nombre), element('small', '', `${reading.origen === 'SENSOR' ? 'Nueva lectura del sensor' : 'Diagnóstico manual'} · ${relativeTime(reading.marca_temporal)}`));
    item.append(copy, element('span', `status-badge ${statusClass(getReadingStatus(reading))}`, prettyStatus(getReadingStatus(reading))));
    item.addEventListener('click', () => {
      selectedPlantId = plant.id;
      navigate('detail');
      renderSelectedPlant();
    });
    list.append(item);
  });
}

function renderAlerts() {
  const root = document.getElementById('alerts-list');
  const selectedPlantFilter = document.getElementById('alert-plant-filter').value || 'all';
  const filtered = alerts.filter((alert) => {
    if (selectedPlantFilter !== 'all' && alert.plantId !== selectedPlantFilter) return false;
    if (alertFilter === 'unread' && alert.read) return false;
    if (alertFilter === 'critical' && !['CRITICO', 'EN_RIESGO', 'DESCONECTADA'].includes(alert.status)) return false;
    return true;
  });
  root.replaceChildren();
  document.getElementById('alerts-empty').classList.toggle('hidden', filtered.length > 0);
  if (!filtered.length) return;
  let currentDay = '';
  filtered.forEach((alert) => {
    const day = new Date(alert.createdAt).toDateString();
    if (day !== currentDay) {
      currentDay = day;
      const label = new Date(alert.createdAt).toDateString() === new Date().toDateString() ? 'Hoy' : formatDate(alert.createdAt);
      root.append(element('h2', 'alert-day', label));
    }
    const row = element('button', `alert-card ${alert.read ? '' : 'is-unread'}`);
    row.type = 'button';
    row.append(element('span', `alert-symbol ${statusClass(alert.status)}`, alert.status === 'CRITICO' ? '!' : alert.status === 'EN_RIESGO' ? '☼' : alert.status === 'DESCONECTADA' ? '⌁' : '✦'));
    const copy = element('span', 'alert-copy');
    copy.append(element('strong', '', alert.plantName), element('span', '', alert.message), element('small', '', relativeTime(alert.createdAt)));
    row.append(copy);
    if (!alert.read) row.append(element('i', 'unread-dot'));
    row.addEventListener('click', () => {
      alert.read = true;
      storeAlerts();
      selectedPlantId = alert.plantId;
      renderAlerts();
      updateAlertCounters();
      navigate('detail');
      renderSelectedPlant();
    });
    root.append(row);
  });
}

function updateAlertCounters() {
  unreadAlerts = alerts.filter((alert) => !alert.read).length;
  const badge = document.getElementById('nav-alert-count');
  badge.textContent = unreadAlerts;
  badge.classList.toggle('hidden', unreadAlerts === 0);
  document.getElementById('notification-dot').classList.toggle('hidden', unreadAlerts === 0);
  const popover = document.getElementById('popover-alerts');
  popover.replaceChildren();
  const latest = alerts.slice(0, 3);
  if (!latest.length) {
    popover.append(element('p', 'muted popover-empty', 'No hay novedades por ahora.'));
  } else {
    latest.forEach((alert) => {
      const row = element('button', 'popover-alert');
      row.type = 'button';
      row.append(element('span', `alert-symbol ${statusClass(alert.status)}`, alert.status === 'CRITICO' ? '!' : '✦'));
      const text = element('span', '');
      text.append(element('strong', '', alert.plantName), element('small', '', alert.message));
      row.append(text);
      row.addEventListener('click', () => {
        selectedPlantId = alert.plantId;
        document.getElementById('notification-popover').classList.add('hidden');
        navigate('detail');
        renderSelectedPlant();
      });
      popover.append(row);
    });
  }
}

function navigate(view) {
  currentView = view;
  document.querySelectorAll('.view').forEach((section) => {
    section.classList.toggle('is-visible', section.dataset.view === view);
  });
  document.querySelectorAll('[data-view-link]').forEach((link) => {
    link.classList.toggle('is-active', link.dataset.viewLink === view);
  });
  document.getElementById('breadcrumb-current').textContent = {
    dashboard: 'Panel de control',
    plants: 'Mis plantas',
    detail: selectedPlant()?.nombre || 'Detalle de planta',
    history: 'Historial',
    manual: 'Diagnóstico manual',
    shared: 'Cuidado compartido',
    alerts: 'Notificaciones',
    settings: 'Configuración',
  }[view] || 'Jardín';
  document.getElementById('notification-popover').classList.add('hidden');
  document.getElementById('sidebar').classList.remove('is-open');
  document.querySelectorAll('.mobile-bottom-nav [data-view-link]').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.viewLink === view || (view === 'detail' && button.dataset.viewLink === 'plants'));
  });
  if (view === 'detail' || view === 'manual' || view === 'history' || view === 'shared') {
    renderSelectedPlant();
  }
  if (view === 'alerts') renderAlerts();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function signOut(message = '') {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = undefined;
  }
  token = '';
  userEmail = '';
  displayName = '';
  plants = [];
  selectedPlantId = '';
  alerts = [];
  deviceCredentials = null;
  lastStatuses.clear();
  localStorage.removeItem('materaToken');
  sessionStorage.removeItem('materaToken');
  localStorage.removeItem('materaEmail');
  localStorage.removeItem('materaName');
  document.getElementById('global-error').classList.add('hidden');
  appShell.classList.add('hidden');
  authPanel.classList.remove('hidden');
  document.body.classList.remove('is-authenticated');
  authForm.reset();
  setAuthMode('login');
  if (message) showMessage(authError, message);
}

function setFilter(group, filter) {
  if (group === 'dashboard') dashboardFilter = filter;
  else plantsFilter = filter;
  const selector = group === 'dashboard' ? '#dashboard-filters' : '#plants-filters';
  document.querySelectorAll(`${selector} .filter-chip`).forEach((button) => {
    button.classList.toggle('is-active', button.dataset.filter === filter);
  });
  renderPlantCards(group === 'dashboard' ? plantGrid : allPlantsGrid, filter, group === 'dashboard' ? '' : document.getElementById('plant-search').value);
}

function openAddPlant() {
  if (!plants.length) {
    addPlantDialog.showModal();
    showPlantStep(1);
  } else {
    addPlantDialog.showModal();
    showPlantStep(1);
  }
}

function showPlantStep(step) {
  document.querySelectorAll('.modal-step').forEach((section) => {
    section.classList.toggle('hidden', Number(section.dataset.step) !== step);
  });
  document.querySelectorAll('[data-step-indicator]').forEach((indicator) => {
    const number = Number(indicator.dataset.stepIndicator);
    indicator.classList.toggle('is-current', number === step);
    indicator.classList.toggle('is-complete', number < step);
    indicator.textContent = number < step ? '✓' : String(number);
  });
}

async function createPlant() {
  const name = document.getElementById('new-plant-name').value.trim();
  const speciesName = document.getElementById('new-plant-species').value;
  if (!name || !speciesName) {
    document.getElementById('add-plant-form').reportValidity();
    return;
  }
  const next = document.getElementById('plant-next');
  next.disabled = true;
  try {
    deviceCredentials = await apiRequest('/plantas', {
      method: 'POST',
      body: JSON.stringify({ nombre: name, especie: speciesName }),
    });
    document.getElementById('new-device-id').textContent = deviceCredentials.dispositivo_id;
    document.getElementById('new-device-token').textContent = deviceCredentials.token_dispositivo;
    document.getElementById('new-plant-credentials').classList.remove('hidden');
    document.getElementById('sensor-waiting-label').textContent = 'Buscando sensor… puedes continuar con valores manuales.';
    showPlantStep(2);
  } catch (error) {
    showNotice('No se pudo agregar la planta', error.message);
  } finally {
    next.disabled = false;
  }
}

async function finishAddPlant() {
  document.getElementById('plant-created-name').textContent = `${deviceCredentials?.nombre || document.getElementById('new-plant-name').value} ya está en tu jardín.`;
  showPlantStep(3);
  try {
    await refreshGarden();
  } catch (error) {
    onApiError(error);
  }
}

function renderManualResult(diagnosis, plant) {
  const root = document.getElementById('manual-result');
  root.replaceChildren();
  const header = element('div', 'manual-result-heading');
  header.append(element('span', 'eyebrow', 'RESULTADO DE DIAGNÓSTICO'), element('h2', '', plant.nombre));
  const badge = element('span', `state-hero ${statusClass(diagnosis.estado)}`);
  badge.append(element('span', 'state-hero-label', prettyStatus(diagnosis.estado)), element('small', '', 'Índice de vitalidad'));
  root.append(header, badge, element('p', 'manual-result-note', 'Resultado basado en los valores que ingresaste.'));
  const params = element('div', 'manual-result-metrics');
  diagnosis.parametros.forEach((parameter) => {
    const item = element('div', 'manual-result-metric');
    item.append(element('span', '', parameter.nombre), element('strong', '', `${parameter.valor} ${parameter.unidad}`), element('small', parameter.estado === 'OPTIMO' ? 'healthy-text' : 'risk-text', parameter.estado));
    params.append(item);
  });
  root.append(params);
  const list = element('ul', 'recommendation-list');
  (diagnosis.recomendaciones.length ? diagnosis.recomendaciones : ['Tu planta está en su rango ideal.']).forEach((text) => {
    list.append(element('li', 'recommendation-item', text));
  });
  root.append(list);
}

async function submitManualDiagnosis(event) {
  event.preventDefault();
  const plant = selectedPlant();
  if (!plant) {
    showNotice('Selecciona una planta', 'Agrega una planta a tu jardín antes de guardar un diagnóstico.');
    return;
  }
  const readings = {
    humedad: Number(document.getElementById('humedad').value),
    luz: Number(document.getElementById('luz').value),
    temperatura: Number(document.getElementById('temperatura').value),
  };
  const limits = { humedad: [0, 100], luz: [0, 200000], temperatura: [-50, 80] };
  let valid = true;
  Object.entries(readings).forEach(([key, value]) => {
    const message = document.getElementById(`${key}-validation`);
    const [min, max] = limits[key];
    const error = !Number.isFinite(value) || value < min || value > max
      ? `${key[0].toUpperCase()}${key.slice(1)} debe estar entre ${min} y ${max}.`
      : '';
    message.textContent = error;
    message.classList.toggle('hidden', !error);
    valid &&= !error;
  });
  if (!valid) return;

  const submit = document.querySelector('#manual-form button[type="submit"]');
  submit.disabled = true;
  try {
    const diagnosis = await apiRequest(`/plantas/${encodeURIComponent(plant.id)}/lecturas`, {
      method: 'POST',
      body: JSON.stringify({ especie: plant.especie, ...readings }),
    });
    renderManualResult(diagnosis, plant);
    await refreshGarden();
    navigate('manual');
    renderManualResult(diagnosis, selectedPlant() || plant);
  } catch (error) {
    showNotice('No se pudo guardar la lectura', error.message);
  } finally {
    submit.disabled = false;
  }
}

function exportHistory() {
  if (!historyFilteredReadings.length) {
    showNotice('No hay lecturas para exportar', 'Elige otra planta o un período con mediciones.');
    return;
  }
  const rows = [
    ['Fecha', 'Origen', 'Especie', 'Humedad', 'Luz', 'Temperatura', 'Estado'],
    ...historyFilteredReadings.map((reading) => [
      reading.marca_temporal,
      reading.origen,
      reading.especie,
      reading.humedad,
      reading.luz,
      reading.temperatura,
      prettyStatus(getReadingStatus(reading)),
    ]),
  ];
  const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n');
  const blob = new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = element('a');
  link.href = url;
  link.download = `historial-${selectedPlant()?.nombre || 'planta'}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function setAuthPasswordVisibility() {
  const password = document.getElementById('contrasena');
  const visible = password.type === 'password';
  password.type = visible ? 'text' : 'password';
  document.getElementById('toggle-password').setAttribute('aria-label', visible ? 'Ocultar contraseña' : 'Mostrar contraseña');
}

loginTab.addEventListener('click', () => setAuthMode('login'));
registerTab.addEventListener('click', () => setAuthMode('register'));
authForm.addEventListener('submit', authenticate);
document.getElementById('toggle-password').addEventListener('click', setAuthPasswordVisibility);
document.getElementById('forgot-password').addEventListener('click', () => showNotice(
  'Recuperar contraseña',
  'La recuperación de contraseña todavía no está disponible. Contacta con quien administra el jardín para recuperar el acceso.',
));
document.getElementById('logout-button').addEventListener('click', () => signOut());

document.addEventListener('click', (event) => {
  const viewLink = event.target.closest('[data-view-link]');
  if (viewLink) {
    if (viewLink instanceof HTMLAnchorElement) event.preventDefault();
    navigate(viewLink.dataset.viewLink);
    return;
  }
  const action = event.target.closest('[data-action]')?.dataset.action;
  if (!action) return;
  if (action === 'open-add-plant') openAddPlant();
  if (action === 'close-modal') {
    addPlantDialog.close();
    noticeDialog.close();
  }
  if (action === 'invite-collaborator' || action === 'care-unavailable') {
    showNotice('Cuidado compartido', 'La API aún no incluye invitaciones ni acceso compartido. Por ahora tus plantas son privadas y solo tú puedes consultarlas.');
  }
  if (action === 'edit-plant') {
    showNotice('Editar planta', 'La edición de nombre y especie aún no está disponible en la API.');
  }
});

document.querySelectorAll('[data-filter]').forEach((button) => {
  button.addEventListener('click', () => {
    const group = button.closest('#dashboard-filters') ? 'dashboard' : button.closest('#plants-filters') ? 'plants' : null;
    if (group) setFilter(group, button.dataset.filter);
    else {
      setFilter('dashboard', button.dataset.filter);
      navigate('dashboard');
    }
  });
});
document.getElementById('plant-search').addEventListener('input', () => renderPlantCards(allPlantsGrid, plantsFilter, document.getElementById('plant-search').value));
document.getElementById('global-search').addEventListener('input', (event) => {
  const query = event.target.value;
  if (query) {
    navigate('plants');
    document.getElementById('plant-search').value = query;
    renderPlantCards(allPlantsGrid, plantsFilter, query);
  }
});
document.getElementById('notification-button').addEventListener('click', (event) => {
  event.stopPropagation();
  document.getElementById('notification-popover').classList.toggle('hidden');
});
document.addEventListener('click', (event) => {
  if (!event.target.closest('.notification-wrap')) {
    document.getElementById('notification-popover').classList.add('hidden');
  }
});
document.getElementById('menu-toggle').addEventListener('click', () => document.getElementById('sidebar').classList.toggle('is-open'));
document.getElementById('history-plant').addEventListener('change', (event) => {
  selectedPlantId = event.target.value;
  renderSelectedPlant();
});
document.getElementById('shared-plant-select').addEventListener('change', (event) => {
  selectedPlantId = event.target.value;
  renderSelectedPlant();
});
document.getElementById('alert-plant-filter').addEventListener('change', renderAlerts);
document.getElementById('history-source').addEventListener('change', (event) => {
  historySource = event.target.value;
  renderHistory();
});
document.querySelectorAll('[data-period]').forEach((button) => {
  button.addEventListener('click', () => {
    historyPeriod = button.dataset.period;
    document.querySelectorAll('[data-period]').forEach((item) => item.classList.toggle('is-active', item === button));
    renderHistory();
  });
});
document.querySelectorAll('[data-alert-filter]').forEach((button) => {
  button.addEventListener('click', () => {
    alertFilter = button.dataset.alertFilter;
    document.querySelectorAll('[data-alert-filter]').forEach((item) => item.classList.toggle('is-active', item === button));
    renderAlerts();
  });
});
document.getElementById('mark-alerts-read').addEventListener('click', () => {
  alerts.forEach((alert) => { alert.read = true; });
  storeAlerts();
  renderAlerts();
  updateAlertCounters();
});
document.getElementById('export-history').addEventListener('click', exportHistory);
document.getElementById('manual-form').addEventListener('submit', submitManualDiagnosis);
document.querySelectorAll('#manual-form input[type="range"]').forEach((input) => {
  input.addEventListener('input', () => {
    const unit = input.id === 'humedad' ? '%' : input.id === 'luz' ? ' lux' : ' °C';
    document.getElementById(`${input.id}-output`).textContent = `${input.value}${unit}`;
  });
});
document.getElementById('plant-next').addEventListener('click', createPlant);
document.getElementById('plant-finish').addEventListener('click', finishAddPlant);
document.getElementById('plant-done').addEventListener('click', async () => {
  addPlantDialog.close();
  if (deviceCredentials?.id) selectedPlantId = deviceCredentials.id;
  document.getElementById('add-plant-form').reset();
  document.getElementById('new-plant-credentials').classList.add('hidden');
  deviceCredentials = null;
  try {
    await refreshGarden();
    navigate('detail');
  } catch (error) {
    showMessage(document.getElementById('global-error'), error.message);
    navigate('plants');
  }
});
document.getElementById('copy-new-token').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(document.getElementById('new-device-token').textContent);
    document.getElementById('sensor-waiting-label').textContent = 'Token copiado. Guárdalo para configurar el simulador.';
  } catch {
    showNotice('No se pudo copiar', 'Selecciona el token y cópialo manualmente antes de cerrar esta ventana.');
  }
});
document.querySelectorAll('[data-detail-tab]').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-detail-tab]').forEach((tab) => tab.classList.toggle('is-active', tab === button));
    if (button.dataset.detailTab === 'history') navigate('history');
    if (button.dataset.detailTab === 'shared') navigate('shared');
    if (button.dataset.detailTab === 'overview') navigate('detail');
  });
});

if (token) {
  enterApplication().catch((error) => {
    token = '';
    localStorage.removeItem('materaToken');
    authPanel.classList.remove('hidden');
    appShell.classList.add('hidden');
    showMessage(authError, error.message || 'No se pudo recuperar la sesión.');
  });
}
