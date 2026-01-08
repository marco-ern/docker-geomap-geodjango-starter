<template>
  <div class="app-layout">
    <!-- HEADER -->
    <header class="app-header">
      <div class="app-title">
        Visualizador de Sismos
      </div>
      <div class="app-subtitle">
        Selecciona tu ubicación y un sismo para calcular la distancia al epicentro
      </div>
    </header>

    <!-- CONTENIDO PRINCIPAL: MAPA + PANEL DERECHO -->
    <div class="main-content">
      <!-- MAPA -->
      <div id="map" class="map"></div>

      <!-- PANEL DERECHO -->
      <aside class="side-panel">
        <!-- Radios de distancia -->
        <section class="panel-section">
          <h3>Radio de análisis</h3>
          <label>
            <input type="radio" value="150" v-model.number="radioKm" />
            150 km
          </label>
          <label style="margin-left: 12px;">
            <input type="radio" value="380" v-model.number="radioKm" />
            380 km
          </label>
        </section>

        <!-- Info de usuario -->
        <section class="panel-section">
          <h3>Tu ubicación</h3>
          <p>{{ infoUsuario }}</p>
          <small>Tip: haz clic en cualquier punto del mapa para fijar tu ubicación.</small>
        </section>

        <!-- Info de sismo seleccionado -->
        <section class="panel-section">
          <h3>Sismo seleccionado</h3>
          <div v-html="infoSismo"></div>
        </section>

        <!-- Distancia -->
        <section class="panel-section">
          <h3>Distancia</h3>
          <p>{{ infoDistancia }}</p>
        </section>

        <!-- Acordeón de sismos -->
        <section class="panel-section">
          <details open>
            <summary><strong>Lista de sismos</strong></summary>

            <!-- Filtro por magnitud mínima -->
            <div class="mag-filter">
              <label>
                <input type="checkbox" v-model="onlyStrong" />
                Mostrar solo sismos M ≥ 6.5
              </label>
            </div>

            <!-- Buscador -->
            <div class="search-box">
              <input
                v-model="searchText"
                type="text"
                placeholder="Buscar por fecha, id, magnitud, ubicación…"
              />
            </div>

            <!-- Lista -->
            <div class="sismos-list">
              <div v-if="isLoading" class="sismos-empty">
                Cargando sismos...
              </div>

              <template v-else>
                <div
                  v-for="ev in filteredSismos"
                  :key="ev.id"
                  class="sismo-item"
                  @click="onSelectFromList(ev)"
                >
                  <div class="sismo-main">
                    <span
                      class="sismo-mag"
                      :style="{ backgroundColor: getColorPorMagnitud(ev.magnitud) }"
                    >
                      M {{ ev.magnitud.toFixed(1) }}
                    </span>
                    <span class="sismo-title">
                      {{ ev.fecha }} – {{ ev.hora || 'hora N/D' }}
                    </span>
                  </div>
                  <div class="sismo-sub">
                    Prof: {{ ev.profundidad }} km
                    <span v-if="ev.localizacion"> · {{ ev.localizacion }}</span>
                    <span v-if="ev.id" class="sismo-id">ID: {{ ev.id }}</span>
                  </div>
                </div>

                <div v-if="!filteredSismos.length" class="sismos-empty">
                  No se encontraron sismos con ese filtro.
                </div>
              </template>
            </div>
          </details>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const sismos = ref([])          // se llena desde la API
const isLoading = ref(true)
const onlyStrong = ref(false)

const radioKm = ref(150)
const infoUsuario = ref('Selecciona tu ubicación haciendo clic en el mapa.')
const infoSismo = ref('Haz clic en un sismo en el mapa o selecciónalo de la lista.')
const infoDistancia = ref('Distancia: —')
const searchText = ref('')

let mapa
let markerUsuario = null
let circleRadio = null
let sismoSeleccionado = null
let userLatLng = null
const markersPorId = {}

function getColorPorMagnitud(m) {
  if (m >= 8.0) return '#d73027'      // rojo fuerte
  if (m >= 7.5) return '#fc8d59'      // naranja rojizo
  if (m >= 7.0) return '#fee08b'      // amarillo cálido
  if (m >= 6.0) return '#d9ef8b'      // verde amarillento
  if (m >= 5.0) return '#91cf60'      // verde medio
  return '#cccccc'                    // gris para eventos menores
}

function calcularDistanciaKm(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Mapea el JSON del backend a la estructura que consume el front
function mapBackendEventToFront(row, index) {
  const iso = row.fecha_hora_utc || ''
  const [fecha, horaRaw] = iso.split('T')
  const hora = (horaRaw || '').replace('Z', '').slice(0, 8)

  return {
    id: row.id ?? `ev_${index}`,
    lat: Number(row.latitud),
    lon: Number(row.longitud),
    magnitud: Number(row.magnitud),
    fecha: fecha || '',
    hora: hora || '',
    profundidad: Number(row.profundidad_km ?? 0),
    localizacion: row.localizacion || ''
  }
}

function mostrarInfoSismo(ev) {
  infoSismo.value = `
    <strong>Sismo M ${ev.magnitud}</strong><br/>
    Fecha: ${ev.fecha}<br/>
    Hora (UTC): ${ev.hora || 'N/D'}<br/>
    Profundidad: ${ev.profundidad} km<br/>
    ${ev.localizacion ? `Zona: ${ev.localizacion}` : ''}
  `
}

function actualizarCirculoYDistancia() {
  if (!userLatLng || !sismoSeleccionado) {
    infoDistancia.value =
      'Distancia: selecciona tu ubicación y un sismo para calcular.'
    if (circleRadio) {
      mapa.removeLayer(circleRadio)
      circleRadio = null
    }
    return
  }

  const rKm = radioKm.value

  if (circleRadio) {
    mapa.removeLayer(circleRadio)
  }

  circleRadio = L.circle([sismoSeleccionado.lat, sismoSeleccionado.lon], {
    radius: rKm * 1000,
    color: '#3f51b5',
    weight: 2,
    dashArray: '4 4',
    fillColor: '#3f51b5',
    fillOpacity: 0.08
  }).addTo(mapa)

  const d = calcularDistanciaKm(
    userLatLng.lat,
    userLatLng.lng,
    sismoSeleccionado.lat,
    sismoSeleccionado.lon
  )

  let texto = `Distancia entre tu ubicación y el sismo: ${d.toFixed(1)} km`
  if (d <= rKm) {
    texto += ` (dentro del radio de ${rKm} km)`
  } else {
    texto += ` (fuera del radio de ${rKm} km)`
  }

  infoDistancia.value = texto
}

function seleccionarSismo(ev) {
  sismoSeleccionado = ev
  mostrarInfoSismo(ev)
  actualizarCirculoYDistancia()
}

function onSelectFromList(ev) {
  seleccionarSismo(ev)
  const marker = markersPorId[ev.id]
  if (marker) {
    mapa.setView(marker.getLatLng(), 6)
    marker.openPopup?.()
  }
}

const filteredSismos = computed(() => {
  const list = sismos.value
  const text = searchText.value.trim().toLowerCase()

  let result = list
  if (onlyStrong.value) {
    result = result.filter(ev => ev.magnitud >= 6.5)  
  }

  if (!text) return result

  return result.filter(ev => {
    const base = `${ev.id || ''} ${ev.fecha || ''} ${ev.hora || ''} ${ev.magnitud} ${ev.localizacion || ''}`.toLowerCase()
    return base.includes(text)
  })
})

onMounted(async () => {
  // 1. Inicializar mapa
  mapa = L.map('map').setView([19.43, -99.13], 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18
  }).addTo(mapa)

  // 2. Cargar datos desde Django
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  try {
    const resp = await fetch(`${API_BASE_URL}/api/sismos/`)
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    const data = await resp.json()
    const parsed = data.map(mapBackendEventToFront)

    const valid = parsed.filter(
      ev =>
        !Number.isNaN(ev.lat) &&
        !Number.isNaN(ev.lon) &&
        !Number.isNaN(ev.magnitud)
    )

    valid.sort((a, b) => b.magnitud - a.magnitud)
    sismos.value = valid

    // 3. Crear marcadores
    valid.forEach(ev => {
      const color = getColorPorMagnitud(ev.magnitud)

      const marker = L.circleMarker([ev.lat, ev.lon], {
        radius: 5,
        color,
        fillColor: color,
        fillOpacity: 0.85
      }).addTo(mapa)

      markersPorId[ev.id] = marker

      marker.on('click', () => seleccionarSismo(ev))

      const popupText = ev.localizacion
        ? `M ${ev.magnitud} – ${ev.fecha}<br>${ev.localizacion}`
        : `M ${ev.magnitud} – ${ev.fecha}`

      marker.bindPopup(popupText, { offset: [0, -4] })
    })
  } catch (e) {
    console.error('Error cargando sismos desde API Django', e)
    infoSismo.value = 'No se pudieron cargar los sismos desde el servidor.'
  } finally {
    isLoading.value = false
  }

  // 4. Click en el mapa para ubicación del usuario
  mapa.on('click', e => {
    userLatLng = e.latlng

    if (!markerUsuario) {
      markerUsuario = L.marker(userLatLng).addTo(mapa)
    } else {
      markerUsuario.setLatLng(userLatLng)
    }

    infoUsuario.value = `Tu ubicación: ${userLatLng.lat.toFixed(
      3
    )}, ${userLatLng.lng.toFixed(3)}`

    actualizarCirculoYDistancia()
  })
})

watch(radioKm, () => {
  actualizarCirculoYDistancia()
})
</script>

<style scoped>
/* Estilos CSS */
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-header {
  padding: 10px 18px;
  border-bottom: 1px solid #e0e0e0;
  background: #ffffffcc;
  backdrop-filter: blur(4px);
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #222;
}

.app-subtitle {
  font-size: 13px;
  color: #666;
}

.main-content {
  flex: 1;
  display: flex;
  min-height: 0;
}

.map {
  flex: 3;
}

.side-panel {
  flex: 1.4;
  max-width: 380px;
  border-left: 1px solid #2d2f33;
  background: #1f2125;
  color: #f2f2f2;
  padding: 10px 12px;
  font-size: 13px;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 14px;
  border-bottom: 1px solid #2f3237;
  padding-bottom: 8px;
}

.panel-section:last-of-type {
  border-bottom: none;
}

.panel-section h3 {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #e0e0e0;
}

.side-panel p {
  margin: 0 0 4px;
}

.side-panel small {
  color: #9fa3aa;
}

.panel-section label {
  font-size: 13px;
  margin-right: 10px;
}

details summary {
  cursor: pointer;
  color: #f0f0f0;
}

details[open] summary {
  margin-bottom: 6px;
}

.search-box {
  margin: 6px 0 8px;
}

.search-box input {
  width: 100%;
  padding: 5px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #444b55;
  background: #262830;
  color: #f0f0f0;
}

.search-box input::placeholder {
  color: #727784;
}

.sismos-list {
  max-height: 220px;
  overflow-y: auto;
  border-radius: 6px;
  border: 1px solid #30343b;
  background: #15171b;
}

.sismo-item {
  padding: 6px 8px;
  border-bottom: 1px solid #262a31;
  cursor: pointer;
  transition: background 0.15s ease;
}

.sismo-item:last-child {
  border-bottom: none;
}

.sismo-item:hover {
  background: #22262f;
}

.sismo-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sismo-mag {
  display: inline-block;
  min-width: 52px;
  text-align: center;
  padding: 2px 6px;
  border-radius: 999px;
  color: #111;
  font-weight: 700;
  font-size: 11px;
  box-shadow: 0 0 0 1px #00000033;
}

.sismo-title {
  font-size: 13px;
  color: #f3f3f3;
}

.sismo-sub {
  font-size: 11px;
  color: #a0a4af;
  margin-top: 2px;
}

.sismo-id {
  margin-left: 6px;
  color: #888d98;
}

.sismos-empty {
  padding: 8px;
  font-size: 12px;
  color: #999;
}

.sismos-list::-webkit-scrollbar {
  width: 6px;
}
.sismos-list::-webkit-scrollbar-track {
  background: #191b20;
}
.sismos-list::-webkit-scrollbar-thumb {
  background: #424754;
  border-radius: 3px;
}

.mag-filter {
  margin: 4px 0 6px;
  font-size: 12px;
  color: #c7cbd4;
}
.mag-filter input {
  margin-right: 4px;
}
</style>