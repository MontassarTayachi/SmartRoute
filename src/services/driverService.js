import api from './api';
import { normalizeEntityId, unwrapApiData } from './responseAdapter';

const normalizeDriver = (driver) => ({
  id: normalizeEntityId(driver),
  fullName: driver?.fullName ?? driver?.full_name,
  phone: driver?.phone,
  licenseNumber: driver?.licenseNumber ?? driver?.license_number,
  isAvailable:
    typeof driver?.isAvailable === 'boolean'
      ? driver.isAvailable
      : typeof driver?.is_available === 'boolean'
        ? driver.is_available
        : String(driver?.availability ?? '').toLowerCase() === 'available',
});

const normalizeDriverCollection = (payload) => {
  if (Array.isArray(payload)) {
    return payload.map(normalizeDriver);
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
    items: list.map(normalizeDriver),
  };
};

export const getDrivers = async (params = {}) =>
  normalizeDriverCollection(unwrapApiData(await api.get('/drivers', { params })));
export const getDriversWithoutUserAccount = async (params = {}) =>
  normalizeDriverCollection(unwrapApiData(await api.get('/drivers/without-user-account', { params })));
export const createDriver = async (payload) =>
  normalizeDriver(
    unwrapApiData(
      await api.post('/drivers', {
        full_name: payload.fullName,
        phone: payload.phone,
        license_number: payload.licenseNumber,
      }),
    ),
  );
export const updateDriver = async (id, payload) =>
  normalizeDriver(
    unwrapApiData(
      await api.put(`/drivers/${id}`, {
        full_name: payload.fullName,
        phone: payload.phone,
        license_number: payload.licenseNumber,
      }),
    ),
  );
export const assignVehicle = async (id, vehicleId) =>
  unwrapApiData(await api.post(`/drivers/${id}/assign_vehicle`, { vehicle_id: vehicleId }));
