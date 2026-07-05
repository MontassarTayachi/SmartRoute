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
