import api from './api';
import { normalizeEntityId, unwrapApiData } from './responseAdapter';

const normalizeCoordinates = (delivery) => ({
	pickupLatitude: delivery?.pickupLatitude ?? delivery?.pickup_latitude ?? delivery?.pickup_address_lat ?? null,
	pickupLongitude: delivery?.pickupLongitude ?? delivery?.pickup_longitude ?? delivery?.pickup_address_lng ?? null,
	dropoffLatitude: delivery?.dropoffLatitude ?? delivery?.dropoff_latitude ?? delivery?.dropoff_address_lat ?? null,
	dropoffLongitude: delivery?.dropoffLongitude ?? delivery?.dropoff_longitude ?? delivery?.dropoff_address_lng ?? null,
});

const normalizeDelivery = (delivery) => ({
	id: normalizeEntityId(delivery),
	reference: delivery?.reference ?? delivery?.delivery_reference ?? delivery?.code ?? '',
	customer: delivery?.customer ?? delivery?.client ?? delivery?.customer_name ?? '',
	pickupAddress: delivery?.pickupAddress ?? delivery?.pickup_address ?? '',
	dropoffAddress: delivery?.dropoffAddress ?? delivery?.dropoff_address ?? '',
	weightKg: delivery?.weightKg ?? delivery?.weight_kg ?? '',
	priority: delivery?.priority ?? 'medium',
	status: delivery?.status ?? 'pending',
	vehicleId: delivery?.vehicleId ?? delivery?.vehicle_id ?? null,
	vehicle: delivery?.vehicle
		? {
			id: normalizeEntityId(delivery.vehicle),
			registration: delivery.vehicle.registration ?? '',
		}
		: null,
	driverId: delivery?.driverId ?? delivery?.driver_id ?? null,
	driver: delivery?.driver
		? {
			id: normalizeEntityId(delivery.driver),
			fullName: delivery.driver.fullName ?? delivery.driver.full_name ?? '',
		}
		: null,
	scheduledAt: delivery?.scheduledAt ?? delivery?.scheduled_at ?? '',
	createdAt: delivery?.createdAt ?? delivery?.created_at ?? '',
	updatedAt: delivery?.updatedAt ?? delivery?.updated_at ?? '',
	...normalizeCoordinates(delivery),
});

const normalizeCollection = (payload) => {
	if (Array.isArray(payload)) {
		return payload.map(normalizeDelivery);
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
		items: list.map(normalizeDelivery),
	};
};

const toApiPayload = (payload) => ({
	customer: payload.customer,
	pickup_address: payload.pickupAddress,
	dropoff_address: payload.dropoffAddress,
	pickup_address_lat: payload.pickupLatitude,
	pickup_address_lng: payload.pickupLongitude,
	dropoff_address_lat: payload.dropoffLatitude,
	dropoff_address_lng: payload.dropoffLongitude,
	weight_kg: Number(payload.weightKg),
	priority: payload.priority,
	scheduled_at: payload.scheduledAt,
});

export const getDeliveries = async (params = {}) =>
	normalizeCollection(unwrapApiData(await api.get('/deliveries', { params })));

export const getDeliveryById = async (id) =>
	normalizeDelivery(unwrapApiData(await api.get(`/deliveries/${id}`)));

export const createDelivery = async (payload) =>
	normalizeDelivery(unwrapApiData(await api.post('/deliveries', toApiPayload(payload))));

export const updateDelivery = async (id, payload) =>
	normalizeDelivery(unwrapApiData(await api.put(`/deliveries/${id}`, toApiPayload(payload))));

export const assignDelivery = async (id, payload) =>
	normalizeDelivery(unwrapApiData(await api.post(`/deliveries/${id}/assign`, {
		vehicle_id: payload.vehicleId,
		driver_id: payload.driverId,
	})));

export const updateDeliveryStatus = async (id, status) =>
	normalizeDelivery(unwrapApiData(await api.post(`/deliveries/${id}/status`, { status })));
