import api from './api';
import { clearAuth, setRefreshToken, setStoredUser, setToken } from './tokenService';
import {
  extractTokenFromPayload,
  normalizeEntityId,
  normalizeRole,
  unwrapApiData,
} from './responseAdapter';

export const login = async (email, password) => {
  const credentials = new URLSearchParams();
  credentials.append('username', email);
  credentials.append('password', password);

  const response = await api.post('/auth/login', credentials, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  const rawPayload = unwrapApiData(response);
  const payload = {
    ...rawPayload,
    token: extractTokenFromPayload(rawPayload),
    refresh_token: rawPayload?.refresh_token ?? rawPayload?.refreshToken ?? null,
    user: rawPayload?.user
      ? {
          ...rawPayload.user,
        id: normalizeEntityId(rawPayload.user),
          role: normalizeRole(rawPayload.user.role),
        }
      : null,
  };

  if (payload?.token) {
    setToken(payload.token);
  }

  if (payload?.refresh_token) {
    setRefreshToken(payload.refresh_token);
  }

  if (payload?.user) {
    setStoredUser(payload.user);
  }

  return payload;
};

export const refresh = async () => {
  const response = await api.post('/auth/refresh', {
    refresh_token: localStorage.getItem('smartroute_refresh_token'),
  });
  const rawPayload = unwrapApiData(response);
  const payload = {
    ...rawPayload,
    token: extractTokenFromPayload(rawPayload),
    refresh_token: rawPayload?.refresh_token ?? rawPayload?.refreshToken ?? null,
  };

  if (payload?.token) {
    setToken(payload.token);
  }

  if (payload?.refresh_token) {
    setRefreshToken(payload.refresh_token);
  }

  return payload;
};

export const logout = () => {
  clearAuth();
};
