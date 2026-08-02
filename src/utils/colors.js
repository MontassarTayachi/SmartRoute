// Palette de couleurs distinctes attribuées aux livreurs.
// Au-delà de la taille de la palette, une couleur HSL est générée
// de façon déterministe à partir de l'id du livreur.
const PALETTE = [
  "#2563eb", // bleu
  "#f97316", // orange
  "#16a34a", // vert
  "#9333ea", // violet
  "#0891b2", // cyan
  "#db2777", // rose
  "#65a30d", // citron vert
  "#7c3aed", // indigo
  "#0d9488", // teal
  "#ca8a04", // ambre
];

function hashDriverId(driverId) {
  let hash = 0;
  const str = String(driverId);
  for (let i = 0; i < str.length; i += 1) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

export function getDriverColor(driverId, index) {
  if (index != null && index < PALETTE.length) {
    return PALETTE[index];
  }
  const hue = hashDriverId(driverId) % 360;
  return `hsl(${hue}, 70%, 45%)`;
}

/**
 * Construit une map { driverId: couleur } pour une liste de livreurs.
 */
export function buildDriverColorMap(drivers) {
  const map = {};
  drivers.forEach((driver, index) => {
    const id = driver.id ?? driver._id;
    map[id] = getDriverColor(id, index);
  });
  return map;
}
