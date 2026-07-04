import { jwtDecode } from 'jwt-decode';

export const decodeToken = (token) => {
  if (!token) {
    return null;
  }

  try {
    return jwtDecode(token);
  } catch {
    return null;
  }
};

export const isTokenExpired = (token) => {
  const decoded = decodeToken(token);
  if (!decoded?.exp) {
    return true;
  }

  return Date.now() >= decoded.exp * 1000;
};
