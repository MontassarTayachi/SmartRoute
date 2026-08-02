import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import {
  fetchOsrmRoute,
  decodePolyline,
  buildVehicleTrackingWsUrl,
} from "../../services/missionService.js";
import VehicleMarker from "./VehicleMarker.jsx";

const pickupIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:26px;height:26px;border-radius:6px 6px 6px 0;transform:rotate(45deg);
    background:#F5A623;border:2px solid #0B1220;
    box-shadow:0 4px 10px -2px rgba(245,166,35,0.6);
  "></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

const deliveryIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:26px;height:26px;border-radius:6px 6px 6px 0;transform:rotate(45deg);
    background:#2DD4BF;border:2px solid #0B1220;
    box-shadow:0 4px 10px -2px rgba(45,212,191,0.6);
  "></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

// Highlighted pulsing marker for the current guided step
const activeStepIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:30px;height:30px;border-radius:50%;
    background:#10b981;border:3px solid #fff;
    box-shadow:0 0 0 5px rgba(16,185,129,0.3),0 4px 12px rgba(16,185,129,0.5);
  "></div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
  popupAnchor: [0, -18],
});

/** Recentre la carte automatiquement quand les points changent. */
function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points || points.length === 0) return;
    const bounds = L.latLngBounds(points);
    map.fitBounds(bounds, { padding: [48, 48] });
  }, [points, map]);
  return null;
}

/** Vole vers l'étape guidée courante à chaque changement d'étape. */
function FlyToStep({ step }) {
  const map = useMap();
  useEffect(() => {
    if (!step) return;
    map.flyTo([step.lat, step.lng], 15, { duration: 0.8 });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step?.delivery_id, step?.order]);
  return null;
}

export default function DriverMap({ missions, user, activeMission, guidedStepIndex = 0, missionFinished = false }) {
  const [routesByMission, setRoutesByMission] = useState({});
  const [guidedRouteCoords, setGuidedRouteCoords] = useState([]);
  const [isTracking, setIsTracking] = useState(false);
  const [vehiclePosition, setVehiclePosition] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const watchIdRef = useRef(null);
  const wsRef = useRef(null);

  const guidedSteps = useMemo(
    () => activeMission
      ? [...(activeMission.deliveries_order || [])].sort((a, b) => a.order - b.order)
      : [],
    [activeMission]
  );
  const guidedStep = !missionFinished ? (guidedSteps[guidedStepIndex] ?? null) : null;

  const allSteps = useMemo(
    () =>
      missions.flatMap((mission) =>
        [...(mission.deliveries_order || [])].sort((a, b) => a.order - b.order)
      ),
    [missions]
  );

  const allPoints = useMemo(
    () => allSteps.map((step) => [step.lat, step.lng]),
    [allSteps]
  );

  const mapCenter = allPoints[0] || [37.04, 9.66];

  // Charge le trajet réel de chaque mission : polyline existante (décodée)
  // ou calcul OSRM à partir des étapes ordonnées.
  useEffect(() => {
    let cancelled = false;

    async function loadRoutes() {
      const entries = await Promise.all(
        missions.map(async (mission) => {
          if (mission.polyline) {
            return [mission._id, decodePolyline(mission.polyline)];
          }
          const steps = [...(mission.deliveries_order || [])].sort(
            (a, b) => a.order - b.order
          );
          try {
            const route = await fetchOsrmRoute(
              steps.map((s) => ({ lat: s.lat, lng: s.lng }))
            );
            return [mission._id, route];
          } catch (err) {
            console.error(`Route OSRM indisponible pour la mission ${mission._id}:`, err);
            return [mission._id, steps.map((s) => [s.lat, s.lng])];
          }
        })
      );
      if (!cancelled) {
        setRoutesByMission(Object.fromEntries(entries));
      }
    }

    if (missions.length > 0) loadRoutes();
    return () => {
      cancelled = true;
    };
  }, [missions]);

  // Route guidée : position courante (ou étape précédente) → étape active
  useEffect(() => {
    if (!guidedStep) { setGuidedRouteCoords([]); return; }
    let cancelled = false;
    async function loadGuided() {
      const origin = vehiclePosition
        ? { lat: vehiclePosition[0], lng: vehiclePosition[1] }
        : (guidedSteps[guidedStepIndex - 1] ?? null);
      try {
        const pts = origin ? [origin, { lat: guidedStep.lat, lng: guidedStep.lng }] : null;
        const route = pts ? await fetchOsrmRoute(pts) : [];
        if (!cancelled) setGuidedRouteCoords(route);
      } catch {
        if (!cancelled) setGuidedRouteCoords([]);
      }
    }
    loadGuided();
    return () => { cancelled = true; };
  // Recalcule seulement quand l'étape change, pas à chaque update GPS
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guidedStep?.delivery_id, guidedStep?.order]);

  // Démarre le suivi GPS automatiquement dès que la navigation guidée commence
  useEffect(() => {
    if (activeMission && !isTracking) startTracking();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeMission?._id]);

  // Prépare (sans forcer la connexion) le websocket de suivi véhicule.
  const connectTrackingSocket = useCallback(() => {
    try {
      const url = buildVehicleTrackingWsUrl();
      const socket = new WebSocket(url);

      socket.onopen = () => console.log("[tracking] WebSocket connecté:", url);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (typeof payload.lat === "number" && typeof payload.lng === "number") {
            setVehiclePosition([payload.lat, payload.lng]);
            setLastUpdate(payload.updated_at || new Date().toISOString());
          }
        } catch (err) {
          console.warn("[tracking] Message WebSocket illisible:", err);
        }
      };
      socket.onerror = (err) => console.warn("[tracking] Erreur WebSocket:", err);
      socket.onclose = () => console.log("[tracking] WebSocket fermé.");

      wsRef.current = socket;
    } catch (err) {
      console.warn("[tracking] Connexion WebSocket impossible pour le moment:", err);
    }
  }, []);

  const startTracking = useCallback(() => {
    if (!navigator.geolocation) {
      console.warn("Géolocalisation non disponible sur ce navigateur.");
      return;
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setVehiclePosition([pos.coords.latitude, pos.coords.longitude]);
        setLastUpdate(new Date().toISOString());
      },
      (err) => console.warn("Erreur de géolocalisation:", err),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
    );

    connectTrackingSocket();
    setIsTracking(true);
  }, [connectTrackingSocket]);

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsTracking(false);
  }, []);

  useEffect(() => {
    return () => stopTracking();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleTracking = () => (isTracking ? stopTracking() : startTracking());

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={mapCenter}
        zoom={13}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {guidedStep
          ? <FlyToStep step={guidedStep} />
          : (allPoints.length > 0 && <FitBounds points={allPoints} />)}

        {missions.map((mission) => (
          <Polyline
            key={`route-${mission._id}`}
            positions={routesByMission[mission._id] || []}
            pathOptions={{ color: "#4C7DFF", weight: 4, opacity: activeMission ? 0.25 : 0.8 }}
          />
        ))}

        {guidedRouteCoords.length > 1 && (
          <Polyline
            positions={guidedRouteCoords}
            pathOptions={{ color: "#10b981", weight: 5, opacity: 0.9, dashArray: "10 5" }}
          />
        )}

        {allSteps.map((step, idx) => {
          const isGuided = guidedStep
            && step.delivery_id === guidedStep.delivery_id
            && step.step_type === guidedStep.step_type;
          return (
          <Marker
            key={`${step.delivery_id}-${step.step_type}-${idx}`}
            position={[step.lat, step.lng]}
            icon={isGuided ? activeStepIcon : (step.step_type === "pickup" ? pickupIcon : deliveryIcon)}
          >
            <Popup>
              <div className="text-sm space-y-1 min-w-[160px]">
                <p
                  className={`font-display font-semibold ${
                    step.step_type === "pickup" ? "text-cyan" : "text-brand-light"
                  }`}
                >
                  {step.step_type === "pickup" ? "Ramassage" : "Livraison"} · étape{" "}
                  {step.order + 1}
                </p>
                <p>{step.address}</p>
                <p className="font-mono text-xs text-secondary">
                  {step.lat.toFixed(5)}, {step.lng.toFixed(5)}
                </p>
              </div>
            </Popup>
          </Marker>
          );
        })}

        <VehicleMarker
          position={vehiclePosition}
          driverName={user?.name}
          vehicleLabel={missions[0]?.vehicle_id}
          lastUpdate={lastUpdate}
        />
      </MapContainer>

      {/* Légende compacte, ne masque pas la carte */}
      <div className="pointer-events-none absolute top-4 left-4 z-[1000] hidden sm:flex items-center gap-3 rounded-full border border-border/60 bg-surface/90 backdrop-blur px-3 py-1.5 shadow-sm">
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-secondary">
          <span className="h-2 w-2 rounded-sm" style={{ background: "#F5A623" }} />
          Ramassage
        </span>
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-secondary">
          <span className="h-2 w-2 rounded-sm bg-cyan" />
          Livraison
        </span>
      </div>

      {/* Destination en cours de navigation */}
      {guidedStep && !missionFinished && (
        <div className="pointer-events-none absolute inset-x-4 bottom-16 z-[1001] rounded-2xl border border-border/80 bg-surface/95 px-4 py-3 shadow-lg backdrop-blur-xl">
          <p className="text-[10px] uppercase tracking-wider text-tertiary">Destination en cours</p>
          <p className="mt-1 text-sm font-semibold">
            {guidedStep.step_type === "pickup" ? "Ramassage" : "Livraison"} · étape {guidedStep.order + 1}
          </p>
          {guidedStep.address && (
            <p className="mt-0.5 truncate text-xs text-secondary">{guidedStep.address}</p>
          )}
        </div>
      )}

      {/* Bannière de fin de mission */}
      {missionFinished && (
        <div className="pointer-events-none absolute inset-x-4 top-16 z-[1001] flex items-center gap-3 rounded-2xl border border-brand/30 bg-surface/95 px-4 py-3 shadow-lg backdrop-blur-xl">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand/20 text-brand-light">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-bold text-brand-light">Mission terminée !</p>
            <p className="text-xs text-tertiary">Toutes les étapes ont été complétées avec succès.</p>
          </div>
        </div>
      )}

      {/* Contrôle de suivi — coin de la carte, jamais en barre fixe pleine largeur */}
      <button
        onClick={toggleTracking}
        className={`absolute top-4 right-4 z-[1000] flex items-center gap-2 rounded-full px-4 py-2 font-display text-xs font-semibold shadow-sm backdrop-blur transition-all duration-200 ${
          isTracking
            ? "bg-brand text-white hover:brightness-110"
            : "bg-surface/90 border border-border hover:border-brand"
        }`}
      >
        <span className={`h-2 w-2 rounded-full ${isTracking ? "bg-white animate-pulse" : "bg-brand"}`} />
        {isTracking ? "Suivi en cours…" : "Ma position"}
      </button>
    </div>
  );
}