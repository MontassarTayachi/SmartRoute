import { useEffect, useMemo, useState } from 'react';
import VehicleTrackingMap from '../components/VehicleTrackingMap';
import { useToast } from '../context/ToastContext';
import { getApiErrorMessage } from '../utils/apiError';
import { getDrivers } from '../services/driverService';
import { getVehicles } from '../services/vehicleService';
import useVehiclesTracking from '../hooks/useVehiclesTracking';

const formatDateTime = (value) => {
	if (!value) return '-';
	const date = new Date(value);
	return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString('fr-FR');
};

const formatRelative = (value) => {
	if (!value) return '-';
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return '-';
	const diffSec = Math.round((Date.now() - date.getTime()) / 1000);
	if (diffSec < 5) return "à l'instant";
	if (diffSec < 60) return `il y a ${diffSec}s`;
	const min = Math.round(diffSec / 60);
	if (min < 60) return `il y a ${min} min`;
	return formatDateTime(value);
};

const CarIcon = ({ size = 16, color = 'currentColor' }) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<path
			d="M5 16.5V18a1 1 0 001 1h1a1 1 0 001-1v-1h8v1a1 1 0 001 1h1a1 1 0 001-1v-1.5M5 16.5l1.2-5.2A2 2 0 018.14 9.7h7.72a2 2 0 011.94 1.6l1.2 5.2M5 16.5h14"
			stroke={color}
			strokeWidth="1.6"
			strokeLinecap="round"
			strokeLinejoin="round"
		/>
		<circle cx="8" cy="16.5" r="1.3" fill={color} />
		<circle cx="16" cy="16.5" r="1.3" fill={color} />
	</svg>
);

const SearchIcon = () => (
	<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		<circle cx="11" cy="11" r="7" stroke="#94a3b8" strokeWidth="2" />
		<path d="M20 20l-3.2-3.2" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
	</svg>
);

const VehicleTrackingPage = () => {
	const toast = useToast();
	const [vehicles, setVehicles] = useState([]);
	const [drivers, setDrivers] = useState([]);
	const [selectedVehicleId, setSelectedVehicleId] = useState('');
	const [loading, setLoading] = useState(false);
	const [search, setSearch] = useState('');
	const {
		socketState,
		initialLoading,
		lastUpdateAt,
		locationsByVehicleId,
		trackedVehicleIds,
	} = useVehiclesTracking({
		onError: (error) => toast.error(getApiErrorMessage(error, 'Impossible de suivre les véhicules en temps réel')),
	});

	const selectedVehicle = useMemo(
		() => vehicles.find((vehicle) => String(vehicle.id) === String(selectedVehicleId)) ?? null,
		[vehicles, selectedVehicleId],
	);

	const trackedLocations = useMemo(() => {
		return Object.entries(locationsByVehicleId).map(([vehicleId, location]) => ({
			vehicleId,
			latitude: Number(location.latitude),
			longitude: Number(location.longitude),
			timestamp: location.timestamp ?? null,
		}));
	}, [locationsByVehicleId]);

	const selectedLocation = useMemo(() => {
		if (!selectedVehicleId) return null;
		return trackedLocations.find((location) => String(location.vehicleId) === String(selectedVehicleId)) ?? null;
	}, [trackedLocations, selectedVehicleId]);

	const trackedIdSet = useMemo(() => new Set(trackedVehicleIds.map(String)), [trackedVehicleIds]);

	const websocketStatusLabel = socketState === 'connected'
		? 'En direct'
		: socketState === 'loading'
			? 'Connexion...'
			: socketState === 'error'
				? 'Erreur'
				: socketState === 'disconnected'
					? 'Reconnexion...'
					: 'Inactif';

	const vehiclesById = useMemo(() => {
		return vehicles.reduce((accumulator, vehicle) => {
			if (vehicle?.id != null) {
				accumulator[String(vehicle.id)] = vehicle;
			}
			return accumulator;
		}, {});
	}, [vehicles]);

	const filteredVehicles = useMemo(() => {
		if (!search.trim()) return vehicles;
		const q = search.trim().toLowerCase();
		return vehicles.filter((vehicle) =>
			[vehicle.registration, vehicle.status, vehicle.brand, vehicle.model]
				.filter(Boolean)
				.some((field) => String(field).toLowerCase().includes(q)),
		);
	}, [vehicles, search]);

	useEffect(() => {
		const loadData = async () => {
			setLoading(true);
			try {
				const [vehiclesData, driversData] = await Promise.all([
					getVehicles({ page: 1, size: 100 }),
					getDrivers({ page: 1, size: 100 }),
				]);

				setVehicles(Array.isArray(vehiclesData) ? vehiclesData : vehiclesData?.items ?? vehiclesData?.results ?? vehiclesData?.data ?? []);
				setDrivers(Array.isArray(driversData) ? driversData : driversData?.items ?? driversData?.results ?? driversData?.data ?? []);
			} catch (requestError) {
				toast.error(getApiErrorMessage(requestError, 'Impossible de charger le suivi des véhicules'));
			} finally {
				setLoading(false);
			}
		};

		loadData();
	}, [toast]);

	useEffect(() => {
		if (!selectedVehicleId && trackedVehicleIds.length > 0) {
			setSelectedVehicleId(String(trackedVehicleIds[0]));
		}
	}, [selectedVehicleId, trackedVehicleIds]);

	return (
		<section className="page-panel">
			<div className="resource-header">
				<div>
					<h1>Suivi des véhicules</h1>
					<p>Visualisez les véhicules sur OpenStreetMap et suivez leur position en temps réel.</p>
				</div>
			</div>

			<style>{`
				.vtp-layout {
					display: grid;
					grid-template-columns: 280px 1fr;
					gap: 14px;
					align-items: start;
				}

				/* Barre de statut compacte, une seule ligne */
				.vtp-statusbar {
					display: flex;
					align-items: center;
					gap: 10px;
					flex-wrap: wrap;
					padding: 10px 12px;
					border-radius: 12px;
					background: rgba(255, 255, 255, 0.04);
					border: 1px solid rgba(148, 163, 184, 0.16);
					font-size: 12px;
					margin-bottom: 12px;
				}
				.vtp-statusbar .vtp-sep { width: 1px; height: 16px; background: rgba(148, 163, 184, 0.25); }
				.vtp-status-pill { display: inline-flex; align-items: center; gap: 6px; font-weight: 600; }
				.vtp-badge { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; flex-shrink: 0; }
				.vtp-badge-connected { background: #22c55e; box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15); }
				.vtp-statusbar .vtp-muted { color: #64748b; }
				.vtp-statusbar .vtp-strong { font-weight: 700; }

				/* Panneau latéral */
				.vtp-panel {
					display: flex;
					flex-direction: column;
					gap: 8px;
					border: 1px solid rgba(148, 163, 184, 0.16);
					border-radius: 16px;
					background: rgba(255, 255, 255, 0.03);
					padding: 10px;
					max-height: 620px;
				}
				.vtp-panel-header {
					display: flex;
					align-items: center;
					justify-content: space-between;
					padding: 2px 4px 4px;
				}
				.vtp-panel-header h3 {
					font-size: 12px;
					text-transform: uppercase;
					letter-spacing: 0.05em;
					color: #64748b;
					margin: 0;
				}
				.vtp-panel-count {
					font-size: 11px;
					font-weight: 700;
					color: #475569;
					background: rgba(148, 163, 184, 0.15);
					border-radius: 999px;
					padding: 2px 8px;
				}

				.vtp-search {
					display: flex;
					align-items: center;
					gap: 6px;
					padding: 7px 10px;
					border-radius: 10px;
					background: rgba(148, 163, 184, 0.08);
					border: 1px solid rgba(148, 163, 184, 0.16);
				}
				.vtp-search input {
					border: none;
					outline: none;
					background: transparent;
					font-size: 12.5px;
					width: 100%;
					color: inherit;
				}

				/* Liste compacte, dense, scrollable */
				.vtp-list {
					display: flex;
					flex-direction: column;
					gap: 4px;
					overflow-y: auto;
					padding-right: 2px;
				}
				.vtp-item {
					display: flex;
					align-items: center;
					gap: 10px;
					padding: 7px 9px;
					border-radius: 11px;
					border: 1px solid transparent;
					background: transparent;
					cursor: pointer;
					text-align: left;
					transition: background 0.12s ease, border-color 0.12s ease;
					width: 100%;
				}
				.vtp-item:hover { background: rgba(148, 163, 184, 0.1); }
				.vtp-item-selected {
					background: rgba(37, 99, 235, 0.12);
					border-color: rgba(37, 99, 235, 0.35);
				}
				.vtp-item-avatar {
					position: relative;
					flex-shrink: 0;
					width: 30px;
					height: 30px;
					border-radius: 9px;
					display: flex;
					align-items: center;
					justify-content: center;
					background: rgba(148, 163, 184, 0.18);
					color: #475569;
				}
				.vtp-item-selected .vtp-item-avatar {
					background: #2563eb;
					color: white;
				}
				.vtp-item-live-dot {
					position: absolute;
					top: -2px;
					right: -2px;
					width: 8px;
					height: 8px;
					border-radius: 50%;
					background: #22c55e;
					border: 2px solid var(--panel-bg, #0f172a);
					box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.4);
				}
				.vtp-item-body { min-width: 0; flex: 1; }
				.vtp-item-plate {
					font-size: 13px;
					font-weight: 700;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
				.vtp-item-meta {
					font-size: 11px;
					color: #64748b;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
				.vtp-item-chevron { color: #94a3b8; flex-shrink: 0; }

				.vtp-empty { padding: 16px 8px; text-align: center; font-size: 12.5px; color: #94a3b8; }

				@media (max-width: 860px) {
					.vtp-layout { grid-template-columns: 1fr; }
					.vtp-panel { max-height: 260px; }
				}
			`}</style>

			<div className="vtp-statusbar">
				<span className="vtp-status-pill">
					<span className={`vtp-badge ${socketState === 'connected' ? 'vtp-badge-connected' : ''}`} />
					{websocketStatusLabel}
				</span>
				<span className="vtp-sep" />
				<span className="vtp-muted">Suivis: <span className="vtp-strong">{trackedVehicleIds.length}</span></span>
				<span className="vtp-sep" />
				<span className="vtp-muted">Sélection: <span className="vtp-strong">{selectedVehicle?.registration ?? 'Aucun'}</span></span>
				<span className="vtp-sep" />
				<span className="vtp-muted">MAJ: <span className="vtp-strong">{formatRelative(lastUpdateAt)}</span></span>
			</div>

			<div className="vtp-layout">
				<div className="vtp-panel">
					<div className="vtp-panel-header">
						<h3>Véhicules</h3>
						<span className="vtp-panel-count">{filteredVehicles.length}</span>
					</div>

					<div className="vtp-search">
						<SearchIcon />
						<input
							type="text"
							placeholder="Rechercher une plaque..."
							value={search}
							onChange={(event) => setSearch(event.target.value)}
						/>
					</div>

					<div className="vtp-list">
						{filteredVehicles.length === 0 ? (
							<div className="vtp-empty">Aucun véhicule ne correspond.</div>
						) : (
							filteredVehicles.map((vehicle) => {
								const idStr = String(vehicle.id);
								const isSelected = idStr === String(selectedVehicleId);
								const isLive = trackedIdSet.has(idStr);

								return (
									<button
										type="button"
										key={vehicle.id}
										className={`vtp-item ${isSelected ? 'vtp-item-selected' : ''}`}
										onClick={() => setSelectedVehicleId(idStr)}
									>
										<span className="vtp-item-avatar">
											<CarIcon size={15} color={isSelected ? 'white' : '#475569'} />
											{isLive ? <span className="vtp-item-live-dot" /> : null}
										</span>
										<span className="vtp-item-body">
											<span className="vtp-item-plate">{vehicle.registration ?? `Véhicule ${vehicle.id}`}</span>
											<span className="vtp-item-meta">{vehicle.status ?? 'N/A'}</span>
										</span>
										<span className="vtp-item-chevron">
											<svg width="14" height="14" viewBox="0 0 24 24" fill="none">
												<path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
											</svg>
										</span>
									</button>
								);
							})
						)}
					</div>
				</div>

				<div>
					<VehicleTrackingMap
						locations={trackedLocations}
						selectedVehicleId={selectedVehicleId}
						vehiclesById={vehiclesById}
						color="#ef4444"
						height={560}
					/>
				</div>
			</div>

			{trackedLocations.length > 0 ? null : (
				<div className="resource-empty-state" style={{ marginTop: 16 }}>
					Aucune position reçue pour le moment.
				</div>
			)}

			{loading || initialLoading ? <p className="loading-row">Chargement…</p> : null}
			{selectedVehicleId && drivers.length > 0 ? (
				<p className="resource-subtle-text" style={{ marginTop: 12 }}>
					Conducteurs disponibles dans le système: {drivers.length} • {selectedLocation ? `Position: ${selectedLocation.latitude.toFixed(5)}, ${selectedLocation.longitude.toFixed(5)}` : 'Position indisponible'}
				</p>
			) : null}
		</section>
	);
};

export default VehicleTrackingPage;