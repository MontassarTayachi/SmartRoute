import { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const defaultCenter = [48.8566, 2.3522];

// --- Icône véhicule (pastille + pictogramme voiture), orientable selon le cap ---
const vehicleIcon = ({ color = '#2563eb', selected = false, heading = 0 }) => {
	const size = selected ? 40 : 34;
	const ring = selected
		? `<div class="vtm-pulse" style="--vtm-color:${color}"></div>`
		: '';

	return L.divIcon({
		className: 'vtm-marker',
		html: `
			<div class="vtm-marker-inner" style="width:${size}px;height:${size}px;">
				${ring}
				<div class="vtm-dot" style="background:${color};transform:rotate(${heading}deg);">
					<svg viewBox="0 0 24 24" width="${selected ? 20 : 17}" height="${selected ? 20 : 17}" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M12 2 L19 20 L12 16.5 L5 20 Z" fill="white"/>
					</svg>
				</div>
			</div>
		`,
		iconSize: [size, size],
		iconAnchor: [size / 2, size / 2],
		popupAnchor: [0, -size / 2],
	});
};

// --- Icône du résultat de recherche (pin distinct des véhicules) ---
const searchResultIcon = L.divIcon({
	className: 'vtm-search-marker',
	html: `
		<div class="vtm-search-pin">
			<svg viewBox="0 0 24 32" width="34" height="44" xmlns="http://www.w3.org/2000/svg">
				<path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z" fill="#9333ea"/>
				<circle cx="12" cy="12" r="5" fill="white"/>
			</svg>
		</div>
	`,
	iconSize: [34, 44],
	iconAnchor: [17, 44],
	popupAnchor: [0, -40],
});

// Recadre la carte UNIQUEMENT quand c'est justifié :
//  - premier chargement
//  - un véhicule est ajouté ou retiré de la liste (la "flotte" change)
//  - l'utilisateur sélectionne explicitement un véhicule à suivre
// Un simple déplacement de position (mise à jour socket) ne recadre JAMAIS la carte,
// et si l'utilisateur est en train de faire glisser/zoomer la carte à la main,
// on n'interrompt pas sa navigation.
const AutoFrame = ({ locations, selectedVehicleId }) => {
	const map = useMap();
	const hasFramedOnce = useRef(false);
	const userInteracted = useRef(false);
	const programmatic = useRef(false);
	const lastFleetKey = useRef(null);
	const lastSelectedId = useRef(undefined);

	// Détecte une navigation MANUELLE (drag / zoom au clavier-souris-molette),
	// pour ne plus jamais recentrer tant que l'utilisateur navigue lui-même.
	useEffect(() => {
		const markUserInteraction = () => {
			if (!programmatic.current) userInteracted.current = true;
		};
		map.on('dragstart', markUserInteraction);
		map.on('zoomstart', markUserInteraction);
		return () => {
			map.off('dragstart', markUserInteraction);
			map.off('zoomstart', markUserInteraction);
		};
	}, [map]);

	const frameTo = (fn) => {
		programmatic.current = true;
		fn();
		// Les events dragstart/zoomstart déclenchés par nos propres setView/fitBounds
		// sont synchrones : on relâche le flag juste après.
		setTimeout(() => {
			programmatic.current = false;
		}, 0);
	};

	useEffect(() => {
		if (locations.length === 0) return;

		const fleetKey = locations
			.map((l) => l.vehicleId)
			.sort()
			.join(',');
		const fleetChanged = fleetKey !== lastFleetKey.current;
		const selectionChanged = selectedVehicleId !== lastSelectedId.current;
		lastFleetKey.current = fleetKey;
		lastSelectedId.current = selectedVehicleId;

		// Sélectionner un véhicule = intention explicite de le suivre : on réautorise le recadrage.
		if (selectionChanged && selectedVehicleId) {
			userInteracted.current = false;
		}

		const shouldFrame =
			!hasFramedOnce.current || // premier chargement
			selectionChanged || // nouvelle sélection
			(fleetChanged && !userInteracted.current); // véhicule ajouté/retiré, sans navigation en cours

		if (!shouldFrame) return;

		const selected = locations.find((l) => String(l.vehicleId) === String(selectedVehicleId));

		frameTo(() => {
			if (selected) {
				map.setView([selected.latitude, selected.longitude], Math.max(map.getZoom(), 15), {
					animate: hasFramedOnce.current,
				});
			} else if (locations.length === 1) {
				map.setView([locations[0].latitude, locations[0].longitude], 15, {
					animate: hasFramedOnce.current,
				});
			} else {
				const bounds = L.latLngBounds(locations.map((l) => [l.latitude, l.longitude]));
				map.fitBounds(bounds, { padding: [56, 56], maxZoom: 15, animate: hasFramedOnce.current });
			}
		});

		hasFramedOnce.current = true;
	}, [map, locations, selectedVehicleId]);

	return null;
};

// --- Contrôle de recherche de ville / adresse (Nominatim / OpenStreetMap) ---
// Entièrement autonome : gère son propre état, son propre marqueur temporaire,
// et ne touche jamais aux marqueurs ou à la logique de tracking des véhicules.
const SearchControl = () => {
	const map = useMap();
	const [open, setOpen] = useState(false);
	const [query, setQuery] = useState('');
	const [suggestions, setSuggestions] = useState([]);
	const [loading, setLoading] = useState(false);
	const [showSuggestions, setShowSuggestions] = useState(false);
	const [result, setResult] = useState(null); // { lat, lon, label }
	const inputRef = useRef(null);
	const blurTimeout = useRef(null);

	// Débounce de la requête de géocodage.
	useEffect(() => {
		if (!query || query.trim().length < 3) {
			setSuggestions([]);
			setLoading(false);
			return;
		}

		const controller = new AbortController();
		setLoading(true);

		const timer = setTimeout(async () => {
			try {
				const url = `https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=6&q=${encodeURIComponent(
					query
				)}`;
				const res = await fetch(url, {
					signal: controller.signal,
					headers: { 'Accept-Language': 'fr' },
				});
				const data = await res.json();
				setSuggestions(Array.isArray(data) ? data : []);
			} catch (err) {
				if (err.name !== 'AbortError') setSuggestions([]);
			} finally {
				setLoading(false);
			}
		}, 400);

		return () => {
			clearTimeout(timer);
			controller.abort();
		};
	}, [query]);

	const openPanel = () => {
		setOpen(true);
		setTimeout(() => inputRef.current?.focus(), 50);
	};

	const closePanel = () => {
		setOpen(false);
		setShowSuggestions(false);
		setQuery('');
		setSuggestions([]);
		setResult(null); // le marqueur temporaire disparaît avec le panneau
	};

	const clearQuery = () => {
		setQuery('');
		setSuggestions([]);
		inputRef.current?.focus();
	};

	const selectResult = (place) => {
		const lat = parseFloat(place.lat);
		const lon = parseFloat(place.lon);
		if (Number.isNaN(lat) || Number.isNaN(lon)) return;

		setResult({ lat, lon, label: place.display_name });
		setQuery(place.display_name);
		setSuggestions([]);
		setShowSuggestions(false);
		inputRef.current?.blur();

		// Zoom adapté : on utilise la bounding box renvoyée par Nominatim quand elle existe,
		// sinon on retombe sur un niveau de zoom raisonnable de type "ville".
		if (place.boundingbox && place.boundingbox.length === 4) {
			const [south, north, west, east] = place.boundingbox.map(Number);
			const bounds = L.latLngBounds([south, west], [north, east]);
			map.flyToBounds(bounds, { padding: [48, 48], maxZoom: 16, duration: 0.8 });
		} else {
			map.flyTo([lat, lon], 14, { duration: 0.8 });
		}
	};

	const handleBlur = () => {
		// On laisse le temps au clic sur une suggestion de s'exécuter avant de fermer la liste.
		blurTimeout.current = setTimeout(() => setShowSuggestions(false), 150);
	};

	const handleFocus = () => {
		if (blurTimeout.current) clearTimeout(blurTimeout.current);
		if (suggestions.length > 0) setShowSuggestions(true);
	};

	useEffect(() => {
		setShowSuggestions(suggestions.length > 0 && document.activeElement === inputRef.current);
	}, [suggestions]);

	return (
		<>
			<div className={`vtm-search-control ${open ? 'vtm-search-control--open' : ''}`}>
				{!open ? (
					<button
						type="button"
						className="vtm-search-toggle"
						title="Rechercher une ville ou une adresse"
						onClick={openPanel}
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
							<circle cx="11" cy="11" r="7" stroke="#0f172a" strokeWidth="2" />
							<path d="M21 21l-4.3-4.3" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" />
						</svg>
					</button>
				) : (
					<div className="vtm-search-bar">
						<svg
							className="vtm-search-icon"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<circle cx="11" cy="11" r="7" stroke="#64748b" strokeWidth="2" />
							<path d="M21 21l-4.3-4.3" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
						</svg>

						<input
							ref={inputRef}
							type="text"
							value={query}
							placeholder="Ville, adresse..."
							className="vtm-search-input"
							onChange={(e) => setQuery(e.target.value)}
							onFocus={handleFocus}
							onBlur={handleBlur}
						/>

						{loading && <span className="vtm-search-spinner" aria-hidden="true" />}

						{!loading && query && (
							<button
								type="button"
								className="vtm-search-clear"
								title="Effacer"
								onMouseDown={(e) => e.preventDefault()}
								onClick={clearQuery}
							>
								<svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M6 6l12 12M18 6L6 18" stroke="#94a3b8" strokeWidth="2.4" strokeLinecap="round" />
								</svg>
							</button>
						)}

						<button
							type="button"
							className="vtm-search-close"
							title="Fermer la recherche"
							onMouseDown={(e) => e.preventDefault()}
							onClick={closePanel}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M6 6l12 12M18 6L6 18" stroke="#0f172a" strokeWidth="2.4" strokeLinecap="round" />
							</svg>
						</button>

						{showSuggestions && suggestions.length > 0 && (
							<ul className="vtm-search-suggestions">
								{suggestions.map((place) => (
									<li key={place.place_id}>
										<button
											type="button"
											className="vtm-search-suggestion"
											onMouseDown={(e) => e.preventDefault()}
											onClick={() => selectResult(place)}
										>
											<svg
												width="14"
												height="14"
												viewBox="0 0 24 24"
												fill="none"
												xmlns="http://www.w3.org/2000/svg"
												className="vtm-search-suggestion-pin"
											>
												<path
													d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z"
													transform="scale(0.58) translate(0,0)"
													fill="#9333ea"
												/>
											</svg>
											<span className="vtm-search-suggestion-text">
												<span className="vtm-search-suggestion-main">
													{place.display_name.split(',')[0]}
												</span>
												<span className="vtm-search-suggestion-sub">
													{place.display_name.split(',').slice(1).join(',').trim()}
												</span>
											</span>
										</button>
									</li>
								))}
							</ul>
						)}
					</div>
				)}
			</div>

			{result && (
				<Marker position={[result.lat, result.lon]} icon={searchResultIcon}>
					<Popup>
						<div className="vtm-popup-title">Résultat de recherche</div>
						<div className="vtm-popup-row">📍 {result.label}</div>
					</Popup>
				</Marker>
			)}
		</>
	);
};

const timeAgo = (timestamp) => {
	if (!timestamp) return 'Inconnue';
	const diffMs = Date.now() - new Date(timestamp).getTime();
	const min = Math.round(diffMs / 60000);
	if (min < 1) return "À l'instant";
	if (min < 60) return `Il y a ${min} min`;
	const h = Math.round(min / 60);
	if (h < 24) return `Il y a ${h} h`;
	return new Date(timestamp).toLocaleDateString('fr-FR');
};

const VehicleTrackingMap = ({
	locations = [],
	selectedVehicleId = null,
	vehiclesById = {},
	color = '#2563eb',
	height = 420,
}) => {
	const [manualRecenterKey, setManualRecenterKey] = useState(0);
	const [isFullscreen, setIsFullscreen] = useState(false);
	const shellRef = useRef(null);

	const initialCenter = useMemo(() => {
		const first = locations[0];
		return first ? [first.latitude, first.longitude] : defaultCenter;
	}, []); // valeur uniquement pour le montage initial de la carte

	// Garde l'état du bouton synchronisé si l'utilisateur quitte le plein écran
	// via la touche Échap ou les contrôles du navigateur.
	useEffect(() => {
		const handleChange = () => {
			setIsFullscreen(document.fullscreenElement === shellRef.current);
		};
		document.addEventListener('fullscreenchange', handleChange);
		return () => document.removeEventListener('fullscreenchange', handleChange);
	}, []);

	const toggleFullscreen = () => {
		if (!document.fullscreenElement) {
			shellRef.current?.requestFullscreen?.();
		} else {
			document.exitFullscreen?.();
		}
	};

	return (
		<div
			ref={shellRef}
			className={`tracking-map-shell ${isFullscreen ? 'tracking-map-shell--fullscreen' : ''}`}
			style={{ height: isFullscreen ? '100%' : 'clamp(550px, 60vh, 700px)' }}
		>
			<style>{`
				.tracking-map-shell {
					position: relative;
					width: 100%;
					overflow: hidden;
					border-radius: 20px;
					border: 1px solid rgba(148, 163, 184, 0.18);
					box-shadow: 0 20px 45px rgba(15, 23, 42, 0.14), 0 2px 8px rgba(15, 23, 42, 0.06);
					background: #eef2f7;
				}
				.vehicle-tracking-map { width: 100%; height: 100%; }

				/* Barre d'info flottante */
				.vtm-topbar {
					position: absolute;
					top: 14px;
					left: 14px;
					z-index: 500;
					display: flex;
					align-items: center;
					gap: 8px;
					padding: 8px 14px;
					border-radius: 999px;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
					font: 600 13px/1.2 'Inter', system-ui, sans-serif;
					color: #0f172a;
				}
				.vtm-topbar .vtm-count-dot {
					width: 8px; height: 8px; border-radius: 999px; background: ${color};
					box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
				}

				.vtm-recenter-btn {
					position: absolute;
					top: 14px;
					right: 14px;
					z-index: 500;
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-recenter-btn:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}
				.vtm-recenter-btn:active { transform: translateY(0); }

				.vtm-fullscreen-btn {
					position: absolute;
					top: 14px;
					right: 64px;
					z-index: 500;
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-fullscreen-btn:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}
				.vtm-fullscreen-btn:active { transform: translateY(0); }

				.tracking-map-shell--fullscreen {
					border-radius: 0;
					width: 100vw;
					height: 100vh;
				}

				/* --- Contrôle de recherche (ville / adresse) --- */
				.vtm-search-control {
					position: absolute;
					top: 14px;
					right: 114px;
					z-index: 600;
					display: flex;
					justify-content: flex-end;
					max-width: calc(100% - 128px);
				}
				.vtm-search-control--open { max-width: min(340px, calc(100% - 128px)); }

				.vtm-search-toggle {
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					flex-shrink: 0;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-search-toggle:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}

				.vtm-search-bar {
					position: relative;
					display: flex;
					align-items: center;
					gap: 8px;
					width: min(340px, 100%);
					padding: 0 8px 0 12px;
					height: 40px;
					border-radius: 999px;
					background: rgba(255, 255, 255, 0.95);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
					animation: vtm-search-expand 0.18s ease-out;
				}
				@keyframes vtm-search-expand {
					from { opacity: 0; transform: scaleX(0.85); }
					to { opacity: 1; transform: scaleX(1); }
				}
				.vtm-search-bar { transform-origin: right center; }

				.vtm-search-icon { flex-shrink: 0; }

				.vtm-search-input {
					flex: 1;
					min-width: 0;
					border: none;
					outline: none;
					background: transparent;
					font: 500 13px/1.2 'Inter', system-ui, sans-serif;
					color: #0f172a;
				}
				.vtm-search-input::placeholder { color: #94a3b8; }

				.vtm-search-spinner {
					flex-shrink: 0;
					width: 14px;
					height: 14px;
					border-radius: 999px;
					border: 2px solid rgba(148, 163, 184, 0.35);
					border-top-color: #64748b;
					animation: vtm-spin 0.7s linear infinite;
				}
				@keyframes vtm-spin { to { transform: rotate(360deg); } }

				.vtm-search-clear,
				.vtm-search-close {
					display: flex;
					align-items: center;
					justify-content: center;
					flex-shrink: 0;
					width: 26px;
					height: 26px;
					border-radius: 999px;
					border: none;
					background: rgba(148, 163, 184, 0.14);
					cursor: pointer;
					transition: background 0.15s ease;
				}
				.vtm-search-clear:hover,
				.vtm-search-close:hover { background: rgba(148, 163, 184, 0.28); }

				.vtm-search-suggestions {
					position: absolute;
					top: calc(100% + 8px);
					right: 0;
					width: min(340px, 100%);
					max-height: 280px;
					overflow-y: auto;
					list-style: none;
					margin: 0;
					padding: 6px;
					border-radius: 16px;
					background: rgba(255, 255, 255, 0.98);
					backdrop-filter: blur(10px);
					box-shadow: 0 14px 34px rgba(15, 23, 42, 0.22);
				}
				.vtm-search-suggestion {
					display: flex;
					align-items: flex-start;
					gap: 8px;
					width: 100%;
					padding: 8px 10px;
					border: none;
					background: transparent;
					border-radius: 10px;
					text-align: left;
					cursor: pointer;
					transition: background 0.12s ease;
				}
				.vtm-search-suggestion:hover { background: rgba(147, 51, 234, 0.08); }
				.vtm-search-suggestion-pin { flex-shrink: 0; margin-top: 3px; }
				.vtm-search-suggestion-text {
					display: flex;
					flex-direction: column;
					gap: 1px;
					min-width: 0;
				}
				.vtm-search-suggestion-main {
					font: 600 13px/1.3 'Inter', system-ui, sans-serif;
					color: #0f172a;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
				.vtm-search-suggestion-sub {
					font: 500 11px/1.3 'Inter', system-ui, sans-serif;
					color: #94a3b8;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}

				@media (max-width: 480px) {
					.vtm-search-control { right: 108px; }
					.vtm-search-control--open { max-width: calc(100% - 122px); }
					.vtm-search-bar { width: 100%; }
					.vtm-search-suggestions { width: 100%; }
				}

				/* Marqueur véhicule */
				.vtm-marker-inner {
					position: relative;
					display: flex;
					align-items: center;
					justify-content: center;
				}
				.vtm-dot {
					width: 70%;
					height: 70%;
					border-radius: 999px;
					border: 3px solid white;
					display: flex;
					align-items: center;
					justify-content: center;
					box-shadow: 0 8px 18px rgba(15, 23, 42, 0.35);
					transition: transform 0.4s ease;
				}
				.vtm-pulse {
					position: absolute;
					inset: 0;
					border-radius: 999px;
					background: var(--vtm-color);
					opacity: 0.35;
					animation: vtm-pulse-anim 1.8s ease-out infinite;
				}
				@keyframes vtm-pulse-anim {
					0% { transform: scale(0.6); opacity: 0.45; }
					100% { transform: scale(1.9); opacity: 0; }
				}

				/* Marqueur résultat de recherche */
				.vtm-search-pin {
					filter: drop-shadow(0 8px 10px rgba(147, 51, 234, 0.4));
					animation: vtm-search-pin-drop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
				}
				@keyframes vtm-search-pin-drop {
					from { transform: translateY(-14px); opacity: 0; }
					to { transform: translateY(0); opacity: 1; }
				}

				/* Popup moderne */
				.leaflet-popup-content-wrapper {
					border-radius: 14px;
					box-shadow: 0 14px 34px rgba(15, 23, 42, 0.2);
				}
				.leaflet-popup-content { margin: 12px 14px; }
				.vtm-popup-title {
					font: 700 14px/1.3 'Inter', system-ui, sans-serif;
					color: #0f172a;
					margin-bottom: 4px;
				}
				.vtm-popup-row {
					font: 500 12px/1.5 'Inter', system-ui, sans-serif;
					color: #64748b;
					display: flex;
					align-items: center;
					gap: 6px;
				}
			`}</style>

			<div className="vtm-topbar">
				<span className="vtm-count-dot" />
				{locations.length} véhicule{locations.length > 1 ? 's' : ''} suivi{locations.length > 1 ? 's' : ''}
			</div>

			<button
				type="button"
				className="vtm-recenter-btn"
				title="Recentrer la carte"
				onClick={() => setManualRecenterKey((k) => k + 1)}
			>
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" />
					<circle cx="12" cy="12" r="5.5" stroke="#0f172a" strokeWidth="2" />
				</svg>
			</button>

			<button
				type="button"
				className="vtm-fullscreen-btn"
				title={isFullscreen ? 'Quitter le plein écran' : 'Plein écran'}
				onClick={toggleFullscreen}
			>
				{isFullscreen ? (
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path
							d="M9 4v3a2 2 0 0 1-2 2H4M20 9h-3a2 2 0 0 1-2-2V4M4 15h3a2 2 0 0 1 2 2v3M15 20v-3a2 2 0 0 1 2-2h3"
							stroke="#0f172a"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						/>
					</svg>
				) : (
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path
							d="M4 9V6a2 2 0 0 1 2-2h3M15 4h3a2 2 0 0 1 2 2v3M20 15v3a2 2 0 0 1-2 2h-3M9 20H6a2 2 0 0 1-2-2v-3"
							stroke="#0f172a"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						/>
					</svg>
				)}
			</button>

			<MapContainer center={initialCenter} zoom={13} zoomControl={false} className="vehicle-tracking-map">
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; OpenStreetMap contributors'
				/>
				<AutoFrame
					key={manualRecenterKey}
					locations={locations}
					selectedVehicleId={selectedVehicleId}
				/>
				<SearchControl />
				{locations.map((location) => {
					const vehicleId = String(location.vehicleId);
					const vehicle = vehiclesById[vehicleId];
					const isSelected = String(selectedVehicleId) === vehicleId;
					const markerColor = isSelected ? '#16a34a' : color;

					return (
						<Marker
							key={vehicleId}
							position={[location.latitude, location.longitude]}
							icon={vehicleIcon({
								color: markerColor,
								selected: isSelected,
								heading: location.heading ?? 0,
							})}
						>
							<Popup>
								<div className="vtm-popup-title">
									{vehicle?.registration ?? `Véhicule ${vehicleId}`}
								</div>
								<div className="vtm-popup-row">
									📍 {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
								</div>
								<div className="vtm-popup-row">
									🕒 {location.timestamp ? timeAgo(location.timestamp) : 'MAJ inconnue'}
								</div>
							</Popup>
						</Marker>
					);
				})}
			</MapContainer>
		</div>
	);
};

export default VehicleTrackingMap;