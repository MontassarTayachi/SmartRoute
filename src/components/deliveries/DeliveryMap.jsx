import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const PARIS_CENTER = [48.8566, 2.3522];

// ---------------------------------------------------------------------------
// Icônes "pin" modernes (SVG en dataURL, pas de dépendance externe requise)
// ---------------------------------------------------------------------------
const pinSvg = (color) => `
	<div class="dm-pin-wrap">
		<svg width="34" height="44" viewBox="0 0 34 44" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
					<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(15,23,42,0.35)"/>
				</filter>
			</defs>
			<path filter="url(#shadow)" d="M17 0C7.6 0 0 7.6 0 17c0 12.4 17 27 17 27s17-14.6 17-27C34 7.6 26.4 0 17 0z" fill="${color}"/>
			<circle cx="17" cy="17" r="7" fill="white"/>
		</svg>
	</div>
`;

const markerIcon = (color) =>
	L.divIcon({
		className: 'delivery-map-marker',
		html: pinSvg(color),
		iconSize: [34, 44],
		iconAnchor: [17, 44],
		popupAnchor: [0, -40],
	});

const PICKUP_COLOR = '#3b82f6';
const DROPOFF_COLOR = '#ef4444';

// ---------------------------------------------------------------------------
// Utilitaires
// ---------------------------------------------------------------------------
const getDistanceKm = (a, b) => {
	if (!a || !b) return 0;
	const toRad = (value) => (value * Math.PI) / 180;
	const dLat = toRad(b[0] - a[0]);
	const dLng = toRad(b[1] - a[1]);
	const lat1 = toRad(a[0]);
	const lat2 = toRad(b[0]);
	const hav = Math.sin(dLat / 2) ** 2 + Math.sin(dLng / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);
	return Math.round((2 * 6371 * Math.asin(Math.sqrt(hav))) * 10) / 10;
};

// Itineraire routier via OSRM (donnees OpenStreetMap)
const fetchRouteFromOsm = async (start, end, signal) => {
	if (!start || !end) return { positions: [], distanceKm: 0 };
	const [startLat, startLng] = start;
	const [endLat, endLng] = end;
	const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
	const response = await fetch(url, { signal, headers: { Accept: 'application/json' } });
	if (!response.ok) throw new Error('Routing request failed');

	const data = await response.json();
	if (data?.code !== 'Ok' || !Array.isArray(data?.routes) || data.routes.length === 0) {
		throw new Error('No route found');
	}

	const route = data.routes[0];
	const coordinates = Array.isArray(route?.geometry?.coordinates)
		? route.geometry.coordinates.map(([lng, lat]) => [lat, lng])
		: [];

	return {
		positions: coordinates,
		distanceKm: Math.round(((route.distance ?? 0) / 1000) * 10) / 10,
	};
};

// Géocodage via Nominatim (OpenStreetMap) - recherche par nom de ville/adresse
const geocodeCity = async (query, signal) => {
	if (!query || query.trim().length < 2) return [];
	const url = `https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=5&q=${encodeURIComponent(query)}`;
	const res = await fetch(url, { signal, headers: { Accept: 'application/json' } });
	if (!res.ok) return [];
	const data = await res.json();
	return data.map((item) => ({
		label: item.display_name,
		latitude: parseFloat(item.lat),
		longitude: parseFloat(item.lon),
	}));
};

// Géocodage inverse - utilisé quand on déplace un marqueur pour retrouver une adresse lisible
const reverseGeocode = async (lat, lng, signal) => {
	try {
		const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`;
		const res = await fetch(url, { signal, headers: { Accept: 'application/json' } });
		if (!res.ok) return null;
		const data = await res.json();
		return data?.display_name ?? null;
	} catch {
		return null;
	}
};

// ---------------------------------------------------------------------------
// Sous-composants map
// ---------------------------------------------------------------------------
const FitBounds = ({ points }) => {
	const map = useMap();

	useEffect(() => {
		if (points.length === 2) {
			map.fitBounds(points, { padding: [60, 60] });
		} else if (points.length === 1) {
			map.setView(points[0], 14);
		}
	}, [map, points]);

	return null;
};

const ResizeMap = () => {
	const map = useMap();

	useEffect(() => {
		map.invalidateSize();
	}, [map]);

	return null;
};

const MapClickHandler = ({ mode, onPickLocation, clickCount, setClickCount }) => {
	useMapEvents({
		click(event) {
			if (mode !== 'create' || !onPickLocation) return;
			const { lat, lng } = event.latlng;

			if (clickCount === 0) {
				onPickLocation({ type: 'pickup', latitude: lat, longitude: lng });
				setClickCount(1);
				return;
			}

			onPickLocation({ type: 'dropoff', latitude: lat, longitude: lng });
			setClickCount(2);
		},
	});

	return null;
};

// ---------------------------------------------------------------------------
// Barre de recherche de ville (pickup / dropoff) avec suggestions
// ---------------------------------------------------------------------------
const CitySearchField = ({ label, color, placeholder, onSelect }) => {
	const [query, setQuery] = useState('');
	const [suggestions, setSuggestions] = useState([]);
	const [loading, setLoading] = useState(false);
	const [open, setOpen] = useState(false);
	const abortRef = useRef(null);
	const debounceRef = useRef(null);

	useEffect(() => {
		if (debounceRef.current) clearTimeout(debounceRef.current);

		if (!query || query.trim().length < 2) {
			setSuggestions([]);
			return;
		}

		debounceRef.current = setTimeout(async () => {
			if (abortRef.current) abortRef.current.abort();
			const controller = new AbortController();
			abortRef.current = controller;
			setLoading(true);
			try {
				const results = await geocodeCity(query, controller.signal);
				setSuggestions(results);
				setOpen(true);
			} catch (err) {
				if (err.name !== 'AbortError') setSuggestions([]);
			} finally {
				setLoading(false);
			}
		}, 400);

		return () => clearTimeout(debounceRef.current);
	}, [query]);

	const handleSelect = (item) => {
		setQuery(item.label);
		setOpen(false);
		setSuggestions([]);
		onSelect(item);
	};

	return (
		<div className="dm-search-field">
			<span className="dm-search-dot" style={{ background: color }} />
			<input
				type="text"
				value={query}
				placeholder={placeholder}
				onChange={(e) => setQuery(e.target.value)}
				onFocus={() => suggestions.length > 0 && setOpen(true)}
				onBlur={() => setTimeout(() => setOpen(false), 150)}
				className="dm-search-input"
			/>
			{loading ? <span className="dm-search-spinner" /> : null}

			{open && suggestions.length > 0 ? (
				<ul className="dm-suggestions">
					{suggestions.map((s, idx) => (
						<li key={idx} onMouseDown={() => handleSelect(s)} className="dm-suggestion-item">
							{s.label}
						</li>
					))}
				</ul>
			) : null}

			<div className="dm-search-label">{label}</div>
		</div>
	);
};

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------
const DeliveryMap = ({
	mode = 'view',
	pickup,
	dropoff,
	onPickLocation,
	height = 420,
	className = '',
	showSearch = true,
}) => {
	const [clickCount, setClickCount] = useState(0);
	const [routePath, setRoutePath] = useState([]);
	const [routeDistanceKm, setRouteDistanceKm] = useState(0);
	const [routeLoading, setRouteLoading] = useState(false);
	const [distanceSource, setDistanceSource] = useState('haversine');

	const pickupPoint = useMemo(() => {
		if (
			pickup?.latitude === null ||
			pickup?.longitude === null ||
			pickup?.latitude === undefined ||
			pickup?.longitude === undefined
		) {
			return null;
		}

		return [Number(pickup.latitude), Number(pickup.longitude)];
	}, [pickup?.latitude, pickup?.longitude]);

	const dropoffPoint = useMemo(() => {
		if (
			dropoff?.latitude === null ||
			dropoff?.longitude === null ||
			dropoff?.latitude === undefined ||
			dropoff?.longitude === undefined
		) {
			return null;
		}

		return [Number(dropoff.latitude), Number(dropoff.longitude)];
	}, [dropoff?.latitude, dropoff?.longitude]);

	useEffect(() => {
		if (mode === 'create') {
			setClickCount(pickupPoint ? 1 : 0);
		}
	}, [mode, pickupPoint]);

	const points = useMemo(() => [pickupPoint, dropoffPoint].filter(Boolean), [pickupPoint, dropoffPoint]);
	const straightDistanceKm = getDistanceKm(pickupPoint, dropoffPoint);
	const distanceKm = routeDistanceKm || straightDistanceKm;
	const canDrag = Boolean(onPickLocation);

	useEffect(() => {
		if (!pickupPoint || !dropoffPoint) {
			setRoutePath([]);
			setRouteDistanceKm(0);
			setRouteLoading(false);
			setDistanceSource('haversine');
			return;
		}

		const controller = new AbortController();
		setRouteLoading(true);

		const loadRoute = async () => {
			try {
				const route = await fetchRouteFromOsm(pickupPoint, dropoffPoint, controller.signal);
				setRoutePath(route.positions);
				setRouteDistanceKm(route.distanceKm);
				setDistanceSource('route');
			} catch (error) {
				if (error.name === 'AbortError') return;
				setRoutePath([pickupPoint, dropoffPoint]);
				setRouteDistanceKm(straightDistanceKm);
				setDistanceSource('haversine');
			} finally {
				if (!controller.signal.aborted) {
					setRouteLoading(false);
				}
			}
		};

		loadRoute();
		return () => controller.abort();
	}, [pickupPoint, dropoffPoint, straightDistanceKm]);

	// Sélection depuis la recherche de ville
	const handleCitySelect = useCallback(
		(type) => (item) => {
			onPickLocation?.({ type, latitude: item.latitude, longitude: item.longitude, label: item.label });
		},
		[onPickLocation]
	);

	// Déplacement d'un marqueur au drag & drop : on met à jour la position + on tente
	// une adresse lisible via géocodage inverse.
	const handleDragEnd = useCallback(
		(type) => async (event) => {
			const { lat, lng } = event.target.getLatLng();
			onPickLocation?.({ type, latitude: lat, longitude: lng });
			const label = await reverseGeocode(lat, lng);
			if (label) {
				onPickLocation?.({ type, latitude: lat, longitude: lng, label });
			}
		},
		[onPickLocation]
	);

	const handleSwap = () => {
		if (!onPickLocation || !pickupPoint || !dropoffPoint) return;
		onPickLocation({ type: 'pickup', latitude: dropoffPoint[0], longitude: dropoffPoint[1], label: dropoff?.label });
		onPickLocation({ type: 'dropoff', latitude: pickupPoint[0], longitude: pickupPoint[1], label: pickup?.label });
	};

	return (
	<div
  className={`delivery-map-shell ${className}`}
  style={{
    height: "clamp(550px, 60vh, 700px)",
  }}
>
			<style>{`
				.delivery-map-shell {
					position: relative;
					width: 100%;
					border-radius: 20px;
					overflow: hidden;
					box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12), 0 2px 6px rgba(15, 23, 42, 0.06);
					border: 1px solid rgba(148, 163, 184, 0.2);
					background: #fff;
					font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
				}
				.delivery-map { width: 100%; height: 100%; z-index: 0; min-height: 200px; }

				.dm-pin-wrap { filter: drop-shadow(0 1px 1px rgba(0,0,0,0.15)); }
				.delivery-map-marker { background: transparent; border: none; }

				/* Barre de recherche flottante */
				.dm-search-bar {
					position: absolute;
					top: 14px;
					left: 14px;
					right: 14px;
					z-index: 500;
					display: flex;
					gap: 10px;
					align-items: center;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(12px) saturate(180%);
					-webkit-backdrop-filter: blur(12px) saturate(180%);
					border-radius: 16px;
					padding: 10px 12px;
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
					border: 1px solid rgba(255, 255, 255, 0.6);
				}
				.dm-search-field {
					position: relative;
					flex: 1;
					display: flex;
					align-items: center;
					gap: 8px;
					background: #fff;
					border-radius: 12px;
					padding: 8px 12px;
					border: 1px solid rgba(148, 163, 184, 0.35);
					transition: border-color 0.15s ease, box-shadow 0.15s ease;
				}
				.dm-search-field:focus-within {
					border-color: #6366f1;
					box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
				}
				.dm-search-dot {
					width: 9px;
					height: 9px;
					border-radius: 50%;
					flex-shrink: 0;
					box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
				}
				.dm-search-input {
					border: none;
					outline: none;
					flex: 1;
					font-size: 13.5px;
					color: #0f172a;
					background: transparent;
					min-width: 0;
				}
				.dm-search-input::placeholder { color: #94a3b8; }
				.dm-search-label {
					position: absolute;
					top: -9px;
					left: 10px;
					font-size: 10px;
					font-weight: 600;
					letter-spacing: 0.04em;
					text-transform: uppercase;
					color: #64748b;
					background: #fff;
					padding: 0 6px;
					border-radius: 6px;
				}
				.dm-search-spinner {
					width: 14px;
					height: 14px;
					border-radius: 50%;
					border: 2px solid rgba(99,102,241,0.25);
					border-top-color: #6366f1;
					animation: dm-spin 0.7s linear infinite;
					flex-shrink: 0;
				}
				@keyframes dm-spin { to { transform: rotate(360deg); } }

				.dm-suggestions {
					position: absolute;
					top: calc(100% + 6px);
					left: 0;
					right: 0;
					background: #fff;
					border-radius: 12px;
					box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
					border: 1px solid rgba(148, 163, 184, 0.25);
					list-style: none;
					margin: 0;
					padding: 6px;
					max-height: 220px;
					overflow-y: auto;
					z-index: 600;
				}
				.dm-suggestion-item {
					padding: 8px 10px;
					font-size: 12.5px;
					color: #334155;
					border-radius: 8px;
					cursor: pointer;
					line-height: 1.35;
				}
				.dm-suggestion-item:hover { background: #f1f5f9; color: #0f172a; }

				.dm-swap-btn {
					flex-shrink: 0;
					width: 34px;
					height: 34px;
					border-radius: 10px;
					border: 1px solid rgba(148, 163, 184, 0.35);
					background: #fff;
					display: flex;
					align-items: center;
					justify-content: center;
					cursor: pointer;
					color: #475569;
					transition: transform 0.15s ease, background 0.15s ease;
				}
				.dm-swap-btn:hover { background: #f8fafc; transform: rotate(180deg); }

				/* Footer info */
				.delivery-map-meta {
					position: absolute;
					bottom: 14px;
					left: 14px;
					z-index: 500;
					display: flex;
					gap: 10px;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(12px) saturate(180%);
					-webkit-backdrop-filter: blur(12px) saturate(180%);
					border-radius: 14px;
					padding: 8px 14px;
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
					border: 1px solid rgba(255, 255, 255, 0.6);
				}
				.delivery-map-meta > div {
					display: flex;
					flex-direction: column;
					padding-right: 12px;
					border-right: 1px solid rgba(148,163,184,0.3);
				}
				.delivery-map-meta > div:last-child { border-right: none; padding-right: 0; }
				.delivery-map-meta strong {
					font-size: 10px;
					text-transform: uppercase;
					letter-spacing: 0.04em;
					color: #64748b;
					font-weight: 600;
				}
				.delivery-map-meta span {
					font-size: 13.5px;
					font-weight: 600;
					color: #0f172a;
				}

				.dm-hint {
					position: absolute;
					bottom: 14px;
					right: 14px;
					z-index: 500;
					background: rgba(15, 23, 42, 0.75);
					color: #fff;
					font-size: 11px;
					padding: 6px 10px;
					border-radius: 10px;
					backdrop-filter: blur(6px);
					max-width: 60%;
					text-align: right;
				}

				/* -------------------------------------------------------------- */
				/* Responsive - tablette (≤ 768px)                                 */
				/* -------------------------------------------------------------- */
				@media (max-width: 768px) {
					.delivery-map-shell { border-radius: 14px; }
					.dm-search-bar { top: 10px; left: 10px; right: 10px; padding: 8px; border-radius: 14px; }
					.dm-search-field { padding: 7px 10px; }
					.dm-search-input { font-size: 13px; }
					.delivery-map-meta { bottom: 10px; left: 10px; padding: 7px 12px; }
				}

				/* -------------------------------------------------------------- */
				/* Responsive - mobile (≤ 560px)                                   */
				/* -------------------------------------------------------------- */
				@media (max-width: 560px) {
					.delivery-map-shell { border-radius: 12px; }

					/* La barre de recherche passe en colonne, avec le bouton swap au centre */
					.dm-search-bar {
						flex-direction: column;
						align-items: stretch;
						gap: 6px;
						padding: 8px;
						border-radius: 16px;
					}
					.dm-search-field { width: 100%; padding: 9px 10px; }
					.dm-search-label { font-size: 9px; top: -8px; }
					.dm-suggestions { max-height: 160px; font-size: 12px; }
					.dm-suggestion-item { font-size: 12px; padding: 7px 9px; }

					.dm-swap-btn {
						align-self: center;
						width: 30px;
						height: 30px;
						transform: rotate(90deg);
						font-size: 13px;
					}
					.dm-swap-btn:hover { transform: rotate(270deg); }

					/* Le panneau meta passe en pleine largeur au-dessus du bord inférieur */
					.delivery-map-meta {
						left: 10px;
						right: 10px;
						bottom: 10px;
						justify-content: space-between;
						padding: 7px 10px;
						border-radius: 12px;
					}
					.delivery-map-meta > div { padding-right: 8px; }
					.delivery-map-meta strong { font-size: 9px; }
					.delivery-map-meta span { font-size: 12px; }

					/* Le hint passe au-dessus de la barre meta pour ne pas se chevaucher */
					.dm-hint {
						left: 10px;
						right: 10px;
						bottom: 58px;
						max-width: none;
						text-align: center;
						font-size: 10.5px;
						padding: 5px 10px;
					}

					/* Pins légèrement réduits pour laisser plus de place à la carte */
					.delivery-map-marker { transform: scale(0.85); transform-origin: bottom center; }
				}

				/* -------------------------------------------------------------- */
				/* Responsive - très petit écran (≤ 380px)                         */
				/* -------------------------------------------------------------- */
				@media (max-width: 380px) {
					.dm-search-input { font-size: 12px; }
					.dm-search-dot { width: 7px; height: 7px; }
					.delivery-map-meta { flex-direction: row; }
					.delivery-map-meta strong { display: none; }
				}
			`}</style>

			{showSearch ? (
				<div className="dm-search-bar">
					<CitySearchField
						label="Départ"
						color={PICKUP_COLOR}
						placeholder="Rechercher une ville ou adresse de départ..."
						onSelect={handleCitySelect('pickup')}
					/>
					<button type="button" className="dm-swap-btn" onClick={handleSwap} title="Inverser départ / arrivée">
						⇄
					</button>
					<CitySearchField
						label="Arrivée"
						color={DROPOFF_COLOR}
						placeholder="Rechercher une ville ou adresse d'arrivée..."
						onSelect={handleCitySelect('dropoff')}
					/>
				</div>
			) : null}

			<MapContainer  zoomControl={false} center={PARIS_CENTER} zoom={12} className="delivery-map">
				<ResizeMap />
				<MapClickHandler mode={mode} onPickLocation={onPickLocation} clickCount={clickCount} setClickCount={setClickCount} />
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; OpenStreetMap contributors'
				/>
				<FitBounds points={points} />
				{pickupPoint ? (
					<Marker
						position={pickupPoint}
						icon={markerIcon(PICKUP_COLOR)}
						draggable={canDrag}
						eventHandlers={canDrag ? { dragend: handleDragEnd('pickup') } : undefined}
					>
						<Popup>
							<strong>Pickup</strong>
							<br />
							{pickup?.label || `${pickupPoint[0].toFixed(5)}, ${pickupPoint[1].toFixed(5)}`}
							{canDrag ? <div style={{ marginTop: 4, fontSize: 11, color: '#64748b' }}>Glissez pour déplacer</div> : null}
						</Popup>
					</Marker>
				) : null}
				{dropoffPoint ? (
					<Marker
						position={dropoffPoint}
						icon={markerIcon(DROPOFF_COLOR)}
						draggable={canDrag}
						eventHandlers={canDrag ? { dragend: handleDragEnd('dropoff') } : undefined}
					>
						<Popup>
							<strong>Dropoff</strong>
							<br />
							{dropoff?.label || `${dropoffPoint[0].toFixed(5)}, ${dropoffPoint[1].toFixed(5)}`}
							{canDrag ? <div style={{ marginTop: 4, fontSize: 11, color: '#64748b' }}>Glissez pour déplacer</div> : null}
						</Popup>
					</Marker>
				) : null}
				{pickupPoint && dropoffPoint ? (
					<Polyline
						positions={routePath.length > 1 ? routePath : [pickupPoint, dropoffPoint]}
						pathOptions={{ color: '#6366f1', weight: 4, opacity: 0.9, lineCap: 'round' }}
					/>
				) : null}
			</MapContainer>

			<div className="delivery-map-meta">
				<div>
					<strong>Distance</strong>
					<span>{routeLoading ? 'Calcul...' : distanceKm ? `${distanceKm} km` : 'N/A'}</span>
				</div>
				<div>
					<strong>Source</strong>
					<span>{distanceSource === 'route' ? 'Route OSM' : 'Estimation'}</span>
				</div>
				<div>
					<strong>Mode</strong>
					<span>{mode === 'create' ? 'Creation' : 'Visualisation'}</span>
				</div>
			</div>

			{mode === 'create' && canDrag ? (
				<div className="dm-hint">
					{clickCount === 0 ? 'Cliquez pour placer le départ' : clickCount === 1 ? 'Cliquez pour placer l\'arrivée' : 'Glissez les points pour ajuster'}
				</div>
			) : null}
		</div>
	);
};

export default DeliveryMap;