/**
 * Décode une chaîne "encoded polyline" (algorithme Google, utilisé aussi
 * par OSRM) en tableau de points [lat, lng] exploitable par Leaflet.
 */
export function decodePolyline(encoded, precision = 5) {
  if (!encoded) return [];

  const factor = 10 ** precision;
  let index = 0;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < encoded.length) {
    let result = 1;
    let shift = 0;
    let byte;

    do {
      byte = encoded.charCodeAt(index) - 63 - 1;
      index += 1;
      result += byte << shift;
      shift += 5;
    } while (byte >= 0x1f);
    lat += result & 1 ? ~(result >> 1) : result >> 1;

    result = 1;
    shift = 0;
    do {
      byte = encoded.charCodeAt(index) - 63 - 1;
      index += 1;
      result += byte << shift;
      shift += 5;
    } while (byte >= 0x1f);
    lng += result & 1 ? ~(result >> 1) : result >> 1;

    coordinates.push([lat / factor, lng / factor]);
  }

  return coordinates;
}
