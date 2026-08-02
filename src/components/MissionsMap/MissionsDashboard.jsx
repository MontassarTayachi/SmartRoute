import { useMemo, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useMissionsWithRoutes } from "../../hooks/useMissionsWithRoutes";
import MissionRoute from "./MissionRoute";
import MapFlyTo from "./MapFlyTo";
import DriverLegend from "./DriverLegend";
import MissionsSidePanel from "./MissionsSidePanel";

// Centre par défaut de la carte (Tunis) tant qu'aucune mission n'est sélectionnée
const DEFAULT_CENTER = [36.8065, 10.1815];
const DEFAULT_ZOOM = 12;

export default function MissionsDashboard() {
  const { missions, driverColorMap, loading, error } = useMissionsWithRoutes();
  const [selectedId, setSelectedId] = useState(null);

  // Liste dédupliquée des livreurs présents dans les missions du jour, pour la légende
  const drivers = useMemo(() => {
    const seen = new Map();
    missions.forEach((mission) => {
      if (mission.driver) {
        seen.set(mission.driver.id ?? mission.driver._id, mission.driver);
      }
    });
    return Array.from(seen.values());
  }, [missions]);

  const selectedMission = missions.find((mission) => mission._id === selectedId) ?? null;
  const selectedBounds =
    selectedMission?.routeCoords?.length > 0 ? selectedMission.routeCoords : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="flex items-center gap-3 text-gray-500">
          <span className="h-4 w-4 rounded-full border-2 border-gray-300 border-t-indigo-600 animate-spin" />
          Chargement des missions du jour…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <p className="text-red-600">Erreur lors du chargement des missions : {error}</p>
      </div>
    );
  }

  return (
    <div className=" page-panel flex flex-col lg:flex-row h-screen bg-gray-50">
      <MissionsSidePanel missions={missions} selectedId={selectedId} onSelect={setSelectedId} />

      <div className="relative h-full w-full">
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          scrollWheelZoom
          className="w-full h-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {missions.map((mission) => (
            <MissionRoute key={mission._id} mission={mission} />
          ))}

          {selectedBounds && <MapFlyTo bounds={selectedBounds} />}
        </MapContainer>

        <DriverLegend drivers={drivers} driverColorMap={driverColorMap} />
      </div>
    </div>
  );
}
