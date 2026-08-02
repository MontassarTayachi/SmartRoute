import { useEffect } from "react";
import { useMap } from "react-leaflet";

/**
 * Centre et zoome automatiquement la carte sur `bounds` (liste de [lat, lng])
 * dès qu'elle change. Ne rend rien à l'écran.
 */
export default function MapFlyTo({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.flyToBounds(bounds, { padding: [60, 60], duration: 0.8, maxZoom: 15 });
    }
  }, [bounds, map]);

  return null;
}
