const API_URL = 'http://127.0.0.1:5000/api/v1';

const form = document.getElementById('diagnostico-form');
const especieSelect = document.getElementById('especie');
const resultadoSection = document.getElementById('resultado');
const resultadoEspecie = document.getElementById('resultado-especie');
const resultadoEstado = document.getElementById('resultado-estado');
const estadoBadge = document.getElementById('estado-badge');
const errorMessage = document.getElementById('error-message');
const listaParametros = document.getElementById('lista-parametros');
const listaRecomendaciones = document.getElementById('lista-recomendaciones');

function mostrarError(mensaje) {
  errorMessage.textContent = mensaje;
  errorMessage.classList.remove('hidden');
}

function ocultarError() {
  errorMessage.textContent = '';
  errorMessage.classList.add('hidden');
}

async function cargarEspecies() {
  try {
    const response = await fetch(`${API_URL}/especies`);
    const data = await response.json();

    const especies = data.especies || [];

    especies.forEach((nombre) => {
      const option = document.createElement('option');
      option.value = nombre;
      option.textContent = nombre;
      especieSelect.appendChild(option);
    });
  } catch (error) {
    console.error('Error cargando especies:', error);
    mostrarError('No se pudieron cargar las especies. Verifica que el backend esté levantado.');
  }
}

function renderResultado(data) {
  ocultarError();
  resultadoEspecie.textContent = data.especie;
  resultadoEstado.textContent = data.estado;
  estadoBadge.textContent = data.estado;

  const badgeColors = {
    SALUDABLE: '#e8f5e9',
    EN_RIESGO: '#fff8e1',
    CRITICO: '#ffebee',
  };

  estadoBadge.style.backgroundColor = badgeColors[data.estado] || '#f3f4f6';

  listaParametros.innerHTML = '';
  (data.parametros || []).forEach((parametro) => {
    const item = document.createElement('li');
    item.textContent = `${parametro.nombre}: ${parametro.valor} ${parametro.unidad} | estado: ${parametro.estado}`;
    listaParametros.appendChild(item);
  });

  listaRecomendaciones.innerHTML = '';
  if (!data.recomendaciones || data.recomendaciones.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'La planta está en rango ideal.';
    listaRecomendaciones.appendChild(item);
  } else {
    data.recomendaciones.forEach((recomendacion) => {
      const item = document.createElement('li');
      item.textContent = recomendacion;
      listaRecomendaciones.appendChild(item);
    });
  }

  resultadoSection.classList.remove('hidden');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    especie: especieSelect.value,
    humedad: Number(document.getElementById('humedad').value),
    luz: Number(document.getElementById('luz').value),
    temperatura: Number(document.getElementById('temperatura').value),
  };

  try {
    const response = await fetch(`${API_URL}/diagnosticos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Error al diagnosticar la planta');
    }

    renderResultado(data);
  } catch (error) {
    console.error('Error:', error);
    mostrarError(error.message || 'Ocurrió un error al diagnosticar la planta.');
  }
});

cargarEspecies();
