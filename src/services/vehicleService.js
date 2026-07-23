import api from './api';
import { normalizeEntityId, unwrapApiData } from './responseAdapter';

const normalizeVehicleList = (vehicleType) => ({
	id: normalizeEntityId(vehicleType),
	name: vehicleType?.name ?? vehicleType?.nom,
	imageUrl: vehicleType?.imageUrl ?? vehicleType?.image_url,
	createdAt: vehicleType?.createdAt ?? vehicleType?.created_at,
});

const normalizeVehicle = (vehicle) => ({
	id: normalizeEntityId(vehicle),
	registration: vehicle?.registration,
	type: vehicle?.type ?? vehicle?.vehicle_type,
	vehicleListId: vehicle?.vehicleListId ?? vehicle?.vehicle_list_id,
	capacityKg: vehicle?.capacityKg ?? vehicle?.capacity_kg,
	status: vehicle?.status,
	avgFuelConsumption: vehicle?.avgFuelConsumption ?? vehicle?.avg_fuel_consumption,
	createdAt: vehicle?.createdAt ?? vehicle?.created_at,
});

const normalizeVehicleCollection = (payload) => {
	if (Array.isArray(payload)) {
		return payload.map(normalizeVehicle);
	}

	if (!payload || typeof payload !== 'object') {
		return payload;
	}

	const list = payload.items ?? payload.results ?? payload.data;
	if (!Array.isArray(list)) {
		return payload;
	}

	return {
		...payload,
		items: list.map(normalizeVehicle),
	};
};

const normalizeVehicleListCollection = (payload) => {
	if (Array.isArray(payload)) {
		return payload.map(normalizeVehicleList);
	}

	if (!payload || typeof payload !== 'object') {
		return payload;
	}

	const list = payload.items ?? payload.results ?? payload.data;
	if (!Array.isArray(list)) {
		return payload;
	}

	return {
		...payload,
		items: list.map(normalizeVehicleList),
	};
};

const normalizeVehicleLocation = (payload) => {
	if (!payload || typeof payload !== 'object') {
		return payload;
	}

	const location = payload.location ?? payload.data ?? payload.position ?? payload;
	return {
		vehicleId:
			normalizeEntityId(location?.vehicle) ??
			location?.vehicle_id ??
			location?.vehicleId ??
			normalizeEntityId(payload?.vehicle) ??
			payload?.vehicle_id ??
			payload?.vehicleId ??
			null,
		latitude: location?.latitude ?? location?.lat ?? null,
		longitude: location?.longitude ?? location?.lng ?? null,
		timestamp: location?.timestamp ?? location?.createdAt ?? location?.updatedAt ?? null,
	};
};

export const getVehicleLocation = async (id) =>
	({
		...normalizeVehicleLocation(unwrapApiData(await api.get(`/vehicles/${id}/location`))),
		vehicleId: id,
	});

export const getVehiclesLocations = async () => {
	const payload = unwrapApiData(await api.get('/vehicles/locations'));
	const list = Array.isArray(payload)
		? payload
		: payload?.items ?? payload?.results ?? payload?.data ?? [];

	if (!Array.isArray(list)) {
		return [];
	}

	return list
		.map(normalizeVehicleLocation)
		.filter((location) => location?.vehicleId != null && location?.latitude != null && location?.longitude != null);
};

export const sendVehicleLocation = async (id, payload) =>
	normalizeVehicleLocation(
		unwrapApiData(
			await api.post(`/vehicles/${id}/location`, {
				latitude: payload.latitude,
				longitude: payload.longitude,
				timestamp: payload.timestamp,
			}),
		),
	);

export const buildVehicleTrackingSocketUrl = (id) => {
	const baseUrl = new URL(import.meta.env.VITE_API_BASE_URL, window.location.origin);
	const protocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:';
	const basePath = baseUrl.pathname.replace(/\/$/, '');
	return `${protocol}//${baseUrl.host}${basePath}/ws/vehicles/${id}/tracking`;
};

export const buildVehiclesTrackingSocketUrl = () => {
	const baseUrl = new URL(import.meta.env.VITE_API_BASE_URL, window.location.origin);
	const protocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:';
	const basePath = baseUrl.pathname.replace(/\/$/, '');
	return `${protocol}//${baseUrl.host}${basePath}/ws/vehicles/tracking`;
};

export const normalizeVehicleLocationEvent = (payload) => {
	if (!payload || typeof payload !== 'object') {
		return null;
	}

	const source = payload.data ?? payload.location ?? payload.position ?? payload;
	const normalized = normalizeVehicleLocation(source);
	if (normalized?.vehicleId == null || normalized?.latitude == null || normalized?.longitude == null) {
		return null;
	}

	return normalized;
};

export const getVehicles = async (params = {}) =>
	normalizeVehicleCollection(unwrapApiData(await api.get('/vehicles', { params })));
export const getVehicleLists = async (params = {}) =>
	normalizeVehicleListCollection(unwrapApiData(await api.get('/vehicle-list', { params })));
export const getVehicleById = async (id) => normalizeVehicle(unwrapApiData(await api.get(`/vehicles/${id}`)));
export const createVehicle = async (payload) =>
	normalizeVehicle(
		unwrapApiData(
			await api.post('/vehicles', {
				registration: payload.registration,
				vehicle_list_id: payload.vehicleListId,
				capacity_kg: payload.capacityKg,
				status: payload.status,
				avg_fuel_consumption: payload.avgFuelConsumption,
			}),
		),
	);
export const updateVehicle = async (id, payload) =>
	normalizeVehicle(
		unwrapApiData(
			await api.put(`/vehicles/${id}`, {
				registration: payload.registration,
				vehicle_list_id: payload.vehicleListId,
				capacity_kg: payload.capacityKg,
				status: payload.status,
				avg_fuel_consumption: payload.avgFuelConsumption,
			}),
		),
	);

export const deleteVehicle = async (id) => unwrapApiData(await api.delete(`/vehicles/${id}`));
export const getAvailableVehicles = async (params = {}) => unwrapApiData(await api.get('/vehicles/dispo', { params }));