import { Marker, Polyline, Popup } from "react-leaflet";
import { createStepIcon } from "./icons";
import { getDriverDisplayName } from "../../utils/driver";

const STEP_LABEL = {
  pickup: "Pickup",
  delivery: "Delivery",
};

function formatDuration(seconds) {
  if (seconds == null) return "-";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${hours} h ${String(rest).padStart(2, "0")}`;
}

export default function MissionRoute({ mission }) {
  const driverName = getDriverDisplayName(mission.driver);

  return (
    <>
      {mission.routeCoords.length > 1 && (
        <Polyline
          positions={mission.routeCoords}
          pathOptions={{ color: mission.color, weight: 5, opacity: 0.8 }}
        >
          <Popup>
            <div className="text-sm space-y-1 min-w-[180px]">
              <p className="font-semibold text-gray-900">{driverName}</p>
              <p>Région : {mission.region_id}</p>
              <p>Livraisons : {mission.delivery_ids?.length ?? 0}</p>
              <p>Poids total : {mission.total_weight} kg</p>
              <p>Distance : {mission.route_distance} km</p>
              <p>Durée : {formatDuration(mission.route_duration)}</p>
              <p>Statut : {mission.status}</p>
            </div>
          </Popup>
        </Polyline>
      )}

      {mission.sortedSteps.map((step) => (
        <Marker
          key={`${mission._id}-${step.delivery_id}-${step.order}`}
          position={[step.lat, step.lng]}
          icon={createStepIcon(step.step_type, mission.color)}
        >
          <Popup>
            <div className="text-sm space-y-1 min-w-[160px]">
              <p className="font-semibold text-gray-900">{driverName}</p>
              <p>{step.address}</p>
              <p>Type : {STEP_LABEL[step.step_type] ?? step.step_type}</p>
              <p>Ordre : {step.order}</p>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}
