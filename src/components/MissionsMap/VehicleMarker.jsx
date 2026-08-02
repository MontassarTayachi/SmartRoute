import { Marker, Popup } from "react-leaflet";
import L from "leaflet";

/**
 * Crée une icône Leaflet "divIcon" pour représenter le véhicule en direct,
 * avec un halo qui pulse pour signaler une position temps réel.
 */
function buildVehicleIcon() {
  return L.divIcon({
    className: "",
    html: `
      <div class="vehicle-marker-pulse">
        <div style="
          width:16px;height:16px;border-radius:9999px;
          background:#4C7DFF;border:2px solid #E8ECF4;
          box-shadow:0 0 0 4px rgba(76,125,255,0.25);
        "></div>
      </div>
    `,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

const vehicleIcon = buildVehicleIcon();

export default function VehicleMarker({ position, driverName, vehicleLabel, lastUpdate }) {
  if (!position) return null;

  return (
    <Marker position={position} icon={vehicleIcon}>
      <Popup>
        <div className="font-body text-sm space-y-1 min-w-[180px]">
          <p className="font-display font-semibold text-brand">{driverName || "Livreur"}</p>
          <p className="text-secondary">
            Véhicule : <span>{vehicleLabel || "—"}</span>
          </p>
          <p className="font-mono text-xs text-secondary">
            {position[0].toFixed(5)}, {position[1].toFixed(5)}
          </p>
          <p className="text-xs text-secondary">
            Mise à jour :{" "}
            <span>
              {lastUpdate ? new Date(lastUpdate).toLocaleTimeString("fr-FR") : "en direct"}
            </span>
          </p>
        </div>
      </Popup>
    </Marker>
  );
}
