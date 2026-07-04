import api from './api';
import { normalizeEntityId, unwrapApiData } from './responseAdapter';

const normalizeVehicle = (vehicle) => ({
	id: normalizeEntityId(vehicle),
	registration: vehicle?.registration,
	type: vehicle?.type ?? vehicle?.vehicle_type,
	capacityKg: vehicle?.capacityKg ?? vehicle?.capacity_kg,
	status: vehicle?.status,
	avgFuelConsumption: vehicle?.avgFuelConsumption ?? vehicle?.avg_fuel_consumption,
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

export const getVehicles = async (params = {}) =>
	normalizeVehicleCollection(unwrapApiData(await api.get('/vehicles', { params })));
export const getVehicleById = async (id) => normalizeVehicle(unwrapApiData(await api.get(`/vehicles/${id}`)));
export const createVehicle = async (payload) =>
	normalizeVehicle(
		unwrapApiData(
			await api.post('/vehicles', {
				registration: payload.registration,
				vehicle_type: payload.type,
				capacity_kg: payload.capacityKg,
				avg_fuel_consumption: payload.avgFuelConsumption,
			}),
		),
	);
export const updateVehicle = async (id, payload) =>
	normalizeVehicle(
		unwrapApiData(
			await api.put(`/vehicles/${id}`, {
				registration: payload.registration,
				vehicle_type: payload.type,
				capacity_kg: payload.capacityKg,
				avg_fuel_consumption: payload.avgFuelConsumption,
			}),
		),
	);
export const deleteVehicle = async (id) => unwrapApiData(await api.delete(`/vehicles/${id}`));
