import L from "leaflet";

// Couleur de remplissage fixe selon le type d'étape (indépendante du livreur)
const TYPE_FILL = {
  pickup: "#16a34a", // vert
  delivery: "#dc2626", // rouge
};

/**
 * Icône en forme de pin : couleur de remplissage = type d'étape
 * (pickup/delivery), couleur du contour = livreur.
 */
export function createStepIcon(stepType, driverColor) {
  const fill = TYPE_FILL[stepType] ?? "#6b7280";
  const html = `
    <div style="width:26px;height:34px;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.35));">
      <svg width="26" height="34" viewBox="0 0 26 34" xmlns="http://www.w3.org/2000/svg">
        <path d="M13 0C5.8 0 0 5.7 0 12.8 0 22.4 13 34 13 34s13-11.6 13-21.2C26 5.7 20.2 0 13 0z"
              fill="${fill}" stroke="${driverColor}" stroke-width="3"/>
        <circle cx="13" cy="13" r="5" fill="white"/>
      </svg>
    </div>
  `;

  return L.divIcon({
    html,
    className: "",
    iconSize: [26, 34],
    iconAnchor: [13, 34],
    popupAnchor: [0, -32],
  });
}
