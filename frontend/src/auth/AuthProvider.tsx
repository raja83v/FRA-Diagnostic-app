import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  AUTH_LOGOUT_EVENT,
  ensureCsrfToken,
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  signup as signupRequest,
} from '../api';
import type { AuthNotice, AuthSessionResponse, AuthUser, LoginPayload, SignupPayload } from '../types';

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authNotice: AuthNotice | null;
  login: (payload: LoginPayload) => Promise<AuthSessionResponse>;
  signup: (payload: SignupPayload) => Promise<AuthSessionResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearAuthNotice: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authNotice, setAuthNotice] = useState<AuthNotice | null>(null);

  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    ensureCsrfToken()
      .catch(() => undefined)
      .finally(() => refreshUser().finally(() => setIsLoading(false)));

    const handleForcedLogout = (event: Event) => {
      const detail = event instanceof CustomEvent ? event.detail : undefined;
      setUser(null);
      setIsLoading(false);
      setAuthNotice({
        kind: 'info',
        message:
          detail?.reason === 'session-expired'
            ? 'Your session expired. Sign in again to continue your work.'
            : 'Authentication required. Sign in to continue.',
      });
    };

    window.addEventListener(AUTH_LOGOUT_EVENT, handleForcedLogout);
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, handleForcedLogout);
  }, []);

  const login = async (payload: LoginPayload) => {
    const session = await loginRequest(payload);
    setUser(session.user);
    setAuthNotice(null);
    return session;
  };

  const signup = async (payload: SignupPayload) => {
    const session = await signupRequest(payload);
    setUser(session.user);
    setAuthNotice(null);
    return session;
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } finally {
      setUser(null);
      setAuthNotice({ kind: 'success', message: 'You have been signed out.' });
    }
  };

  const clearAuthNotice = () => setAuthNotice(null);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      authNotice,
      login,
      signup,
      logout,
      refreshUser,
      clearAuthNotice,
    }),
    [authNotice, isLoading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}