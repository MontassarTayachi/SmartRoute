import { useEffect, useState, useCallback } from "react";
import {
  getConnectedUser,
  getDriverId,
  fetchTodayMissions,
} from "../services/missionService.js";

/**
 * Charge le livreur connecté (localStorage) et ses missions du jour.
 * Expose l'état de chargement, les erreurs et une fonction refresh().
 */
export function useDriverMissions() {
  const [user, setUser] = useState(null);
  const [driverId, setDriverId] = useState(null);
  const [missions, setMissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadMissions = useCallback(async (id, signal) => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await fetchTodayMissions(id, { signal });
      setMissions(items);
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Erreur inconnue lors du chargement des missions.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

useEffect(() => {
  const controller = new AbortController();

  const init = async () => {
    try {
      const connectedUser = await getConnectedUser();

      console.log(connectedUser);

      const id = getDriverId(connectedUser);

      console.log(id);

      setUser(connectedUser);
      setDriverId(id);

      if (!connectedUser || !id) {
        setError("Aucun livreur connecté trouvé.");
        setIsLoading(false);
        return;
      }

      await loadMissions(id, controller.signal);
    } catch (err) {
      console.error(err);
      setError(err.message || "Erreur lors du chargement.");
      setIsLoading(false);
    }
  };

  init();

  return () => controller.abort();
}, [loadMissions]);

  const refresh = useCallback(() => {
    if (driverId) loadMissions(driverId);
  }, [driverId, loadMissions]);

  return { user, driverId, missions, isLoading, error, refresh };
}
