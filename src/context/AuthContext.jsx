import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { login as loginRequest, logout as logoutRequest } from '../services/authService';
import {
  clearAuth,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
} from '../services/tokenService';
import { normalizeRole } from '../services/responseAdapter';
import { decodeToken, isTokenExpired } from '../utils/jwt';

const AuthContext = createContext(null);

const buildUserFromToken = (token, fallbackUser = null) => {
  const decoded = decodeToken(token);
  if (!decoded) {
    return fallbackUser;
  }

  return {
    ...fallbackUser,
    id: decoded.sub ?? decoded.user_id ?? decoded.id ?? fallbackUser?.id ?? null,
    name:
      decoded.name ?? decoded.full_name ?? decoded.preferred_username ?? fallbackUser?.name ?? 'Utilisateur',
    email: decoded.email ?? decoded.username ?? fallbackUser?.email ?? '',
    role: normalizeRole(decoded.role ?? fallbackUser?.role ?? null),
  };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    const storedUser = getStoredUser();

    if (!token || isTokenExpired(token)) {
      clearAuth();
      setUser(null);
      setLoading(false);
      return;
    }

    const restoredUser = buildUserFromToken(token, storedUser);
    if (restoredUser) {
      setUser(restoredUser);
      setStoredUser(restoredUser);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const payload = await loginRequest(email, password);
    const nextUser = payload?.user ?? buildUserFromToken(payload?.token);

    if (payload?.token) {
      setToken(payload.token);
    }

    if (nextUser) {
      setUser(nextUser);
      setStoredUser(nextUser);
    }

    return { ...payload, user: nextUser };
  };

  const logout = () => {
    logoutRequest();
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      login,
      logout,
      loading,
      setUser,
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
};
