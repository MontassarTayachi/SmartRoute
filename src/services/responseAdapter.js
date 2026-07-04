export const unwrapApiData = (response) => {
  const body = response?.data;

  if (body && typeof body === 'object' && 'data' in body) {
    return body.data;
  }

  return body;
};

export const extractTokenFromPayload = (payload) =>
  payload?.token ?? payload?.access_token ?? payload?.accessToken ?? null;

export const normalizeRole = (role) => {
  if (!role || typeof role !== 'string') {
    return role ?? null;
  }

  const upper = role.toUpperCase();
  const aliases = {
    DISPATCHER: 'MANAGER',
    LOGISTIC_MANAGER: 'MANAGER',
    MANAGER: 'MANAGER',
    ADMIN: 'ADMIN',
    DRIVER: 'DRIVER',
  };

  return aliases[upper] ?? upper;
};

export const toApiRole = (role) => {
  if (!role || typeof role !== 'string') {
    return role ?? null;
  }

  const upper = role.toUpperCase();
  const mapping = {
    ADMIN: 'admin',
    MANAGER: 'dispatcher',
    DRIVER: 'driver',
    DISPATCHER: 'dispatcher',
  };

  return mapping[upper] ?? role.toLowerCase();
};

export const normalizeEntityId = (item) => item?.id ?? item?._id ?? null;
