import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  user_id: number;
  email: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  signin: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  signout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  // Ensure we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Load token from localStorage on mount (only on client)
  useEffect(() => {
    if (!isClient || typeof window === 'undefined') return;

    try {
      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('auth_user');

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (error) {
      console.error('Error loading auth from localStorage:', error);
    }
  }, [isClient]);

  const signup = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        // Try to parse error as JSON, fallback to text
        const contentType = response.headers.get('content-type');
        let errorMessage = 'Signup failed';

        if (contentType && contentType.includes('application/json')) {
          try {
            const error = await response.json();
            errorMessage = error.detail || error.message || errorMessage;
          } catch (e) {
            // JSON parsing failed, use default message
            errorMessage = `Signup failed with status ${response.status}`;
          }
        } else {
          // Not JSON, try to read as text
          try {
            const errorText = await response.text();
            errorMessage = errorText || `Signup failed with status ${response.status}`;
          } catch (e) {
            errorMessage = `Signup failed with status ${response.status}`;
          }
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Store token and user info
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('auth_user', JSON.stringify({ user_id: data.user_id, email: data.email }));
        } catch (error) {
          console.error('Error saving auth to localStorage:', error);
        }
      }

      setToken(data.access_token);
      setUser({ user_id: data.user_id, email: data.email });
    } catch (error) {
      // Re-throw if it's already our custom error
      if (error instanceof Error) {
        throw error;
      }
      // Handle network errors or other unexpected errors
      throw new Error('Network error. Please check your connection and try again.');
    }
  };

  const signin = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        // Try to parse error as JSON, fallback to text
        const contentType = response.headers.get('content-type');
        let errorMessage = 'Signin failed';

        if (contentType && contentType.includes('application/json')) {
          try {
            const error = await response.json();
            errorMessage = error.detail || error.message || errorMessage;
          } catch (e) {
            errorMessage = `Signin failed with status ${response.status}`;
          }
        } else {
          try {
            const errorText = await response.text();
            errorMessage = errorText || `Signin failed with status ${response.status}`;
          } catch (e) {
            errorMessage = `Signin failed with status ${response.status}`;
          }
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Store token and user info
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('auth_user', JSON.stringify({ user_id: data.user_id, email: data.email }));
        } catch (error) {
          console.error('Error saving auth to localStorage:', error);
        }
      }

      setToken(data.access_token);
      setUser({ user_id: data.user_id, email: data.email });
    } catch (error) {
      // Re-throw if it's already our custom error
      if (error instanceof Error) {
        throw error;
      }
      // Handle network errors or other unexpected errors
      throw new Error('Network error. Please check your connection and try again.');
    }
  };

  const signout = () => {
    // Clear token and user info
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      } catch (error) {
        console.error('Error clearing auth from localStorage:', error);
      }
    }
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        signin,
        signup,
        signout,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    // Only throw on client-side to avoid SSR issues
    if (typeof window !== 'undefined') {
      throw new Error('useAuth must be used within an AuthProvider');
    }

    // Return safe defaults for SSR
    return {
      user: null,
      token: null,
      signin: async () => { throw new Error('SSR: Auth not available'); },
      signup: async () => { throw new Error('SSR: Auth not available'); },
      signout: () => {},
      isAuthenticated: false,
    };
  }

  return context;
}
