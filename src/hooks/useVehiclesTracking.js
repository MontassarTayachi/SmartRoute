import { useEffect, useMemo, useRef, useState } from 'react';
import {
	buildVehiclesTrackingSocketUrl,
	getVehiclesLocations,
	normalizeVehicleLocationEvent,
} from '../services/vehicleService';

const SOCKET_RECONNECT_DELAY_MS = 3000;

export const useVehiclesTracking = ({ onError } = {}) => {
	const [locationsByVehicleId, setLocationsByVehicleId] = useState({});
	const [socketState, setSocketState] = useState('idle');
	const [initialLoading, setInitialLoading] = useState(true);
	const [lastUpdateAt, setLastUpdateAt] = useState(null);
	const onErrorRef = useRef(onError);

	useEffect(() => {
		onErrorRef.current = onError;
	}, [onError]);

	useEffect(() => {
		let cancelled = false;

		const loadInitialLocations = async () => {
			setInitialLoading(true);
			try {
				const locations = await getVehiclesLocations();
				if (cancelled) return;

				setLocationsByVehicleId(
					locations.reduce((accumulator, location) => {
						accumulator[String(location.vehicleId)] = location;
						return accumulator;
					}, {}),
				);

				const newestTimestamp = locations
					.map((location) => location.timestamp)
					.filter(Boolean)
					.sort()
					.at(-1);
				setLastUpdateAt(newestTimestamp ?? null);
			} catch (error) {
				onErrorRef.current?.(error);
			} finally {
				if (!cancelled) {
					setInitialLoading(false);
				}
			}
		};

		loadInitialLocations();
		return () => {
			cancelled = true;
		};
	}, []);

	useEffect(() => {
		let socket = null;
		let reconnectTimer = null;
		let stopped = false;

		const connectSocket = () => {
			if (stopped) return;

			setSocketState('loading');
			socket = new WebSocket(buildVehiclesTrackingSocketUrl());

			socket.onopen = () => {
				setSocketState('connected');
			};

			socket.onclose = () => {
				if (stopped) return;
				setSocketState('disconnected');
				reconnectTimer = window.setTimeout(connectSocket, SOCKET_RECONNECT_DELAY_MS);
			};

			socket.onerror = (event) => {
				setSocketState('error');
				onErrorRef.current?.(event);
			};

			socket.onmessage = (event) => {
				try {
					const payload = JSON.parse(event.data);
					const nextLocation = normalizeVehicleLocationEvent(payload);
					if (!nextLocation) return;

					const vehicleId = String(nextLocation.vehicleId);
					setLocationsByVehicleId((previous) => {
						const previousLocation = previous[vehicleId];
						if (
							previousLocation &&
							previousLocation.latitude === nextLocation.latitude &&
							previousLocation.longitude === nextLocation.longitude &&
							previousLocation.timestamp === nextLocation.timestamp
						) {
							return previous;
						}

						return {
							...previous,
							[vehicleId]: nextLocation,
						};
					});
					setLastUpdateAt(nextLocation.timestamp ?? new Date().toISOString());
				} catch {
					return;
				}
			};
		};

		connectSocket();

		return () => {
			stopped = true;
			if (reconnectTimer) {
				clearTimeout(reconnectTimer);
			}
			if (socket) {
				socket.close();
			}
		};
	}, []);

	const trackedVehicleIds = useMemo(() => Object.keys(locationsByVehicleId), [locationsByVehicleId]);

	return {
		initialLoading,
		socketState,
		lastUpdateAt,
		locationsByVehicleId,
		trackedVehicleIds,
	};
};

export default useVehiclesTracking;
