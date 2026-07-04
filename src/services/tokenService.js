const TOKEN_KEY = 'smartroute_token';
const REFRESH_TOKEN_KEY = 'smartroute_refresh_token';
const USER_KEY = 'smartroute_user';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);
export const getStoredUser = () => {
  const rawUser = localStorage.getItem(USER_KEY);
  return rawUser ? JSON.parse(rawUser) : null;
};

export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const setRefreshToken = (refreshToken) =>
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
export const setStoredUser = (user) =>
  localStorage.setItem(USER_KEY, JSON.stringify(user));

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};
