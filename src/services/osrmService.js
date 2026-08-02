// Serveur de démo public OSRM par défaut. Configurable via VITE_OSRM_URL
// pour pointer vers une instance auto-hébergée en production.
const OSRM_BASE_URL = import.meta.env.VITE_OSRM_URL || "https://router.project-osrm.org";

/**
 * Calcule un itinéraire routier réel (suivant les routes OSM) entre une
 * série d'étapes ordonnées, via l'API OSRM.
 *
 * @param {Array<{lat: number, lng: number}>} steps - étapes triées par `order`
 * @returns {Promise<Array<[number, number]>>} liste de points [lat, lng]
 */
export async function fetchOsrmRoute(steps) {
  if (!steps || steps.length === 0) return [];
  if (steps.length === 1) return [[steps[0].lat, steps[0].lng]];

  const coordinates = steps.map((step) => `${step.lng},${step.lat}`).join(";");
  const url = `${OSRM_BASE_URL}/route/v1/driving/${coordinates}?overview=full&geometries=geojson`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Erreur OSRM (${response.status})`);
  }

  const data = await response.json();
  const route = data.routes?.[0];
  if (!route) {
    throw new Error("Aucun itinéraire trouvé par OSRM");
  }

  // GeoJSON renvoie [lng, lat] : Leaflet attend [lat, lng]
  return route.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
}
