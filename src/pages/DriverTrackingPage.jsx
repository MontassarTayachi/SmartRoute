import { useEffect, useMemo, useRef, useState } from 'react';
import { getApiErrorMessage } from '../utils/apiError';
import VehicleTrackingMap from '../components/VehicleTrackingMap';
import { getVehicleById, getVehicleLocation, sendVehicleLocation } from '../services/vehicleService';
import { getCurrentDriver } from '../services/driverService';

const DEFAULT_INTERVAL_MS = 7000;

const formatDateTime = (value) => {
	if (!value) return '-';
	const date = new Date(value);
	return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString('fr-FR');
};

const DriverTrackingPage = () => {
	const [driver, setDriver] = useState(null);
	const [driverLoading, setDriverLoading] = useState(true);
	const [loading, setLoading] = useState(true);
	const [trackingEnabled, setTrackingEnabled] = useState(false);
	const [lastSentAt, setLastSentAt] = useState(null);
	const [currentPosition, setCurrentPosition] = useState(null);
	const [vehicle, setVehicle] = useState(null);
	const [error, setError] = useState('');
	const watchIdRef = useRef(null);
	const intervalRef = useRef(null);
	const positionRef = useRef(null);
	const vehicleIdRef = useRef(null);

	// Le conducteur ne vient pas de useAuth() mais d'un appel API dédié.
	// C'est là que se trouve le champ assigned_vehicle_id.
	useEffect(() => {
		let cancelled = false;

		const loadDriver = async () => {
			setDriverLoading(true);
			try {
				const response = await getCurrentDriver();
				const currentDriver = response?.driver ?? null;
				if (!cancelled) {
					setDriver(currentDriver);
					console.log('[DriverTrackingPage] Current driver:', currentDriver);
				}
			} catch (requestError) {
				if (!cancelled) {
					console.error('[DriverTrackingPage] Error fetching current driver:', requestError);
					setError(getApiErrorMessage(requestError, 'Impossible de charger le profil conducteur'));
				}
			} finally {
				if (!cancelled) setDriverLoading(false);
			}
		};

		loadDriver();
		return () => {
			cancelled = true;
		};
	}, []);

	const driverVehicleId = useMemo(() => {
		return driver?.assigned_vehicle_id ?? null;
	}, [driver]);

	useEffect(() => {
		positionRef.current = currentPosition;
	}, [currentPosition]);

	useEffect(() => {
		vehicleIdRef.current = driverVehicleId;
	}, [driverVehicleId]);

	const stopTracking = () => {
		if (watchIdRef.current !== null && navigator.geolocation) {
			navigator.geolocation.clearWatch(watchIdRef.current);
			watchIdRef.current = null;
		}
		if (intervalRef.current) {
			clearInterval(intervalRef.current);
			intervalRef.current = null;
		}
	};

	const pushPosition = async (latitude, longitude) => {
		const vehicleId = vehicleIdRef.current;
		if (!vehicleId) return;

		const timestamp = new Date().toISOString();
		try {
			await sendVehicleLocation(vehicleId, { latitude, longitude, timestamp });
			setLastSentAt(timestamp);
			setError('');
		} catch (requestError) {
			setError(getApiErrorMessage(requestError, 'Impossible d’envoyer la position'));
		}
	};

	const startTracking = async () => {
		console.log('[DriverTrackingPage] startTracking() appelé, driverVehicleId =', driverVehicleId);

		if (!driverVehicleId) {
			setError('Aucun véhicule n’est assigné à ce conducteur.');
			return;
		}

		if (!window.isSecureContext) {
			setError('Le GPS nécessite HTTPS ou localhost. Ouvre l’application dans un contexte sécurisé.');
			return;
		}

		if (!navigator.geolocation) {
			setError('La géolocalisation n’est pas disponible dans ce navigateur.');
			return;
		}

		const onSuccess = (position) => {
			console.log('[DriverTrackingPage] position obtenue', position.coords);
			const nextPosition = [position.coords.latitude, position.coords.longitude];
			setCurrentPosition(nextPosition);
			setTrackingEnabled(true);
		};

		const onError = (permissionError) => {
			console.error('[DriverTrackingPage] erreur géolocalisation', permissionError);
			if (permissionError?.code === 1) {
				setError('Autorisation GPS refusée. Active-la dans les paramètres du navigateur.');
			} else if (permissionError?.code === 2) {
				setError('Position GPS indisponible. Vérifie que la localisation est activée.');
			} else if (permissionError?.code === 3) {
				setError('Le GPS a mis trop de temps à répondre. Réessaie.');
			} else {
				setError('Impossible de récupérer la position GPS. Vérifie les permissions.');
			}
			setTrackingEnabled(false);
		};

		navigator.geolocation.getCurrentPosition(onSuccess, onError, {
			enableHighAccuracy: true,
			timeout: 10000,
			maximumAge: 0,
		});
	};

	useEffect(() => {
		let cancelled = false;

		const loadData = async () => {
			setLoading(true);
			setError('');

			try {
				if (!driverVehicleId) {
					setVehicle(null);
					setCurrentPosition(null);
					return;
				}

				const [vehicleData, locationData] = await Promise.all([
					getVehicleById(driverVehicleId),
					getVehicleLocation(driverVehicleId).catch(() => null),
				]);

				if (cancelled) return;

				setVehicle(vehicleData);
				if (locationData?.latitude != null && locationData?.longitude != null) {
					setCurrentPosition([Number(locationData.latitude), Number(locationData.longitude)]);
					setLastSentAt(locationData.timestamp ?? null);
				}
			} catch (requestError) {
				if (!cancelled) {
					setError(getApiErrorMessage(requestError, 'Impossible de charger le véhicule du conducteur'));
				}
			} finally {
				// Sécurité : on force loading à false même en cas de blocage inattendu
				if (!cancelled) setLoading(false);
			}
		};

		loadData();

		// Filet de sécurité supplémentaire : si loadData ne se termine jamais
		// (promesse qui ne résout ni ne rejette), on débloque le bouton après 8s.
		const safetyTimeout = window.setTimeout(() => {
			if (!cancelled) {
				console.warn('[DriverTrackingPage] loading forcé à false après timeout de sécurité');
				setLoading(false);
			}
		}, 8000);

		return () => {
			cancelled = true;
			window.clearTimeout(safetyTimeout);
		};
	}, [driverVehicleId]);

	useEffect(() => {
		if (!trackingEnabled) {
			stopTracking();
			return;
		}

		if (!navigator.geolocation) {
			setError('La géolocalisation n’est pas disponible dans ce navigateur.');
			setTrackingEnabled(false);
			return;
		}

		watchIdRef.current = navigator.geolocation.watchPosition((position) => {
			const nextPosition = [position.coords.latitude, position.coords.longitude];
			setCurrentPosition(nextPosition);
			pushPosition(position.coords.latitude, position.coords.longitude);
		}, (permissionError) => {
			if (permissionError?.code === 1) {
				setError('Autorisation GPS refusée.');
			} else {
				setError('Impossible de récupérer la position GPS.');
			}
			setTrackingEnabled(false);
		}, {
			enableHighAccuracy: true,
			maximumAge: 5000,
			timeout: 10000,
		});

		intervalRef.current = window.setInterval(() => {
			const position = positionRef.current;
			if (position) {
				pushPosition(position[0], position[1]);
			}
		}, DEFAULT_INTERVAL_MS);

		return () => {
			stopTracking();
		};
	}, [trackingEnabled]);

	const toggleTracking = () => {
		console.log('[DriverTrackingPage] toggleTracking() cliqué, trackingEnabled =', trackingEnabled);
		if (trackingEnabled) {
			setTrackingEnabled(false);
			stopTracking();
			return;
		}

		startTracking();
	};

	const isButtonDisabled = driverLoading || loading || !driverVehicleId;

	return (
		<section className="page-panel">
			<div className="resource-header">
				<div>
					<h1>Suivi GPS conducteur</h1>
					<p>Activez le partage de position pour envoyer automatiquement votre localisation.</p>
				</div>
			</div>

			<style>{`
				.tracking-summary {
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
					gap: 12px;
					margin-bottom: 16px;
				}
				.tracking-card {
					padding: 14px 16px;
					border-radius: 16px;
					background: rgba(255, 255, 255, 0.05);
					border: 1px solid rgba(148, 163, 184, 0.18);
				}
				.tracking-card strong { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; margin-bottom: 4px; }
				.tracking-card span { font-size: 14px; font-weight: 600; }
				.tracking-status { display: inline-flex; align-items: center; gap: 8px; }
				.tracking-dot { width: 10px; height: 10px; border-radius: 50%; background: #94a3b8; }
				.tracking-dot-active { background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.15); }
				.tracking-dot-off { background: #f59e0b; }
			`}</style>

			<div className="tracking-summary">
				<div className="tracking-card">
					<strong>Véhicule assigné</strong>
					<span>{vehicle?.registration ?? driverVehicleId ?? 'Aucun'}</span>
				</div>
				<div className="tracking-card">
					<strong>Statut</strong>
					<span className="tracking-status">
						<span className={`tracking-dot ${trackingEnabled ? 'tracking-dot-active' : 'tracking-dot-off'}`} />
						{trackingEnabled ? 'Suivi activé' : 'Suivi désactivé'}
					</span>
				</div>
				<div className="tracking-card">
					<strong>Dernière position envoyée</strong>
					<span>{formatDateTime(lastSentAt)}</span>
				</div>
				<div className="tracking-card">
					<strong>Position courante</strong>
					<span>{currentPosition ? `${currentPosition[0].toFixed(5)}, ${currentPosition[1].toFixed(5)}` : 'En attente'}</span>
				</div>
			</div>

			<div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
				<button type="button" className="btn-primary" onClick={toggleTracking} disabled={isButtonDisabled}>
					{trackingEnabled ? 'Désactiver le tracking' : 'Activer le suivi GPS'}
				</button>
				<span className="resource-subtle-text">
					Envoi automatique toutes les quelques secondes 
				</span>
			</div>

			{/* Message explicite qui dit POURQUOI le bouton est désactivé,
			   au lieu de laisser l'utilisateur cliquer dans le vide. */}
			{isButtonDisabled ? (
				<div className="form-error" style={{ marginBottom: 12 }}>
					{driverLoading || loading
						? 'Chargement des données du conducteur et du véhicule en cours…'
						: 'Aucun véhicule n’est assigné à ton compte conducteur — le bouton reste désactivé tant que ce n’est pas corrigé côté back-end/profil utilisateur.'}
				</div>
			) : null}

			{error ? <div className="form-error" style={{ marginBottom: 12 }}>{error}</div> : null}
			{loading ? <p className="loading-row">Chargement…</p> : null}

			<VehicleTrackingMap
				position={currentPosition}
				label={vehicle?.registration}
				color="#22c55e"
				height={460}
			/>
		</section>
	);
};

export default DriverTrackingPage;