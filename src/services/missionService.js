const API_BASE_URL = import.meta.env.VITE_API_BASE_URLL || "http://localhost:8000/api";

/**
 * Récupère la liste des missions du jour.
 * @returns {Promise<Array>} le tableau `items` renvoyé par l'API
 */
import {getCurrentDriver, getDriversWithoutUserAccount } from './driverService'
export async function getTodayMissions() {
  const response = await fetch(`${API_BASE_URL}/missions/today`);

  if (!response.ok) {
    throw new Error(`Erreur lors de la récupération des missions (${response.status})`);
  }

  const data = await response.json();
  return data.items ?? [];
}
const OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving";

/**
 * Récupère l'utilisateur connecté depuis le localStorage.
 * Clé utilisée par l'application SmartRoute : "smartroute_user".
 */
export async function getConnectedUser() {
  try {
    const data = await getCurrentDriver();
      return data.driver ?? null;
  } catch (err) {
    console.error("Impossible de récupérer le driver :", err);
    return null;
  }
}

export function getDriverId(driver) {
  return driver?._id ?? driver?.id ?? null;
}

/**
 * Récupère les missions du jour pour un livreur donné.
 * GET /api/missions/driver/{driverId}/today
 */
export async function fetchTodayMissions(driverId, { signal } = {}) {
  if (!driverId) {
    throw new Error("driverId manquant : impossible de charger les missions.");
  }
  console.log(driverId);
  const response = await fetch(`${API_BASE_URL}/missions/driver/${driverId}/today`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status} lors du chargement des missions.`);
  }

  const data = await response.json();
  return Array.isArray(data?.items) ? data.items : [];
}

/**
 * Calcule un itinéraire réel via OSRM entre une liste ordonnée de points.
 * Renvoie une liste de coordonnées [lat, lng] prêtes pour un <Polyline>.
 * N'est utilisé que si mission.polyline est null.
 */
export async function fetchOsrmRoute(points) {
  if (!points || points.length < 2) return [];

  const coordsParam = points.map((p) => `${p.lng},${p.lat}`).join(";");
  const url = `${OSRM_BASE_URL}/${coordsParam}?overview=full&geometries=geojson`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Erreur OSRM ${response.status}`);
  }

  const data = await response.json();
  const geometry = data?.routes?.[0]?.geometry?.coordinates;
  if (!geometry) return [];

  // GeoJSON renvoie [lng, lat] -> on inverse pour Leaflet [lat, lng]
  return geometry.map(([lng, lat]) => [lat, lng]);
}

/**
 * Décode une chaîne polyline encodée (algorithme Google/OSRM, précision 5)
 * en tableau de coordonnées [lat, lng].
 */
export function decodePolyline(encoded, precision = 5) {
  if (!encoded) return [];
  const factor = Math.pow(10, precision);
  let index = 0;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    const deltaLat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += deltaLat;

    shift = 0;
    result = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    const deltaLng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += deltaLng;

    coordinates.push([lat / factor, lng / factor]);
  }

  return coordinates;
}

/** URL du websocket de suivi véhicule (à adapter selon l'hôte de déploiement). */
export function buildVehicleTrackingWsUrl(host = "localhost:8000") {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${host}/api/v1/ws/vehicles/tracking`;
}

/**
 * Met à jour le statut d'une étape de mission.
 * PATCH /api/missions/{mission_id}/step
 * @param {string} missionId - ID de la mission
 * @param {number} stepIndex - Index de l'étape dans deliveries_order
 * @param {boolean} isDone - Nouvel état de l'étape (true = terminée)
 */
export async function updateMissionStep(missionId, stepIndex, isDone = true) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE_URL}/missions/${missionId}/step`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      step_index: stepIndex,
      is_done: isDone,
    }),
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status} lors de la mise à jour de l'étape`);
  }

  return await response.json();
}
