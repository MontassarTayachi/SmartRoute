import api from './api';
import { normalizeEntityId, normalizeRole, toApiRole, unwrapApiData } from './responseAdapter';

const normalizeUser = (user) => ({
	id: normalizeEntityId(user),
	name: user?.name,
	email: user?.email,
	role: normalizeRole(user?.role),
	createdAt: user?.createdAt ?? user?.created_at,
});

const normalizeUserCollection = (payload) => {
	if (Array.isArray(payload)) {
		return payload.map(normalizeUser);
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
		items: list.map(normalizeUser),
	};
};

export const getUsers = async (params = {}) => normalizeUserCollection(unwrapApiData(await api.get('/users', { params })));
export const getUserById = async (id) => normalizeUser(unwrapApiData(await api.get(`/users/${id}`)));
export const createUser = async (payload) =>
	normalizeUser(
		unwrapApiData(
			await api.post('/users', {
				name: payload.name,
				email: payload.email,
				password: payload.password,
				role: toApiRole(payload.role),
				is_active: payload.isActive ?? true,
			}),
		),
	);
export const updateUser = async (id, payload) =>
	normalizeUser(
		unwrapApiData(
			await api.put(`/users/${id}`, {
				...payload,
				role: toApiRole(payload.role),
			}),
		),
	);
export const deleteUser = async (id) => unwrapApiData(await api.delete(`/users/${id}`));
