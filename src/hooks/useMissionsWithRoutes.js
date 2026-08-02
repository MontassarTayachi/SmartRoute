import { useEffect, useState } from "react";
import { getTodayMissions } from "../services/missionService";
import { getDrivers } from "../services/driverService";
import { fetchOsrmRoute } from "../services/osrmService";
import { decodePolyline } from "../utils/polylineDecoder";
import { buildDriverColorMap } from "../utils/colors";

/**
 * Récupère les missions du jour, les enrichit avec le livreur associé,
 * l'itinéraire routier (polyline existante ou calculée via OSRM) et une
 * couleur unique par livreur.
 */
export function useMissionsWithRoutes() {
  const [missions, setMissions] = useState([]);
  const [driverColorMap, setDriverColorMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [rawMissions, driversResponse] = await Promise.all([
          getTodayMissions(),
          getDrivers(),
        ]);

        // getDrivers() peut renvoyer un tableau ou un objet paginé { items: [...] }
        const drivers = Array.isArray(driversResponse)
          ? driversResponse
          : driversResponse?.items ?? [];

        const colorMap = buildDriverColorMap(drivers);
        const driversById = new Map(drivers.map((driver) => [driver.id ?? driver._id, driver]));

        const enrichedMissions = await Promise.all(
          rawMissions.map(async (mission) => {
            const driver = driversById.get(mission.driver_id) ?? null;
            const sortedSteps = [...(mission.deliveries_order ?? [])].sort(
              (a, b) => a.order - b.order
            );

            let routeCoords = [];
            try {
              routeCoords = mission.polyline
                ? decodePolyline(mission.polyline)
                : await fetchOsrmRoute(sortedSteps);
            } catch (routeError) {
              // En cas d'échec OSRM, on retombe sur une ligne droite entre étapes
              // plutôt que de ne rien afficher.
              console.error(`Itinéraire indisponible pour la mission ${mission._id}:`, routeError);
              routeCoords = sortedSteps.map((step) => [step.lat, step.lng]);
            }

            return {
              ...mission,
              driver,
              sortedSteps,
              routeCoords,
              color: colorMap[mission.driver_id] ?? "#6b7280",
            };
          })
        );

        if (!cancelled) {
          setMissions(enrichedMissions);
          setDriverColorMap(colorMap);
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? "Erreur inconnue");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { missions, driverColorMap, loading, error };
}